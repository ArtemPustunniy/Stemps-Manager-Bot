from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler

from bot.utils.role_manager import role_manager
from bot.utils.stats_manager import stats_manager
from google_sheets.manager import GoogleSheetManager
import logging
from bot.config.settings import OPENAI_API_KEY
from openai import AsyncOpenAI
import json

openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

ADD_TASKS = 2


async def process_new_tasks(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    message_text = update.message.text.strip()

    spreadsheet_name = context.user_data.get("spreadsheet_name")
    manager_id = context.user_data.get("manager_id")
    if not spreadsheet_name or not manager_id:
        await update.message.reply_text(
            "Ошибка: данные менеджера не найдены. Начните заново с /start_work_day."
        )
        return ConversationHandler.END

    sheet_manager = GoogleSheetManager(spreadsheet_name)
    new_tasks = []

    if message_text.lower() == "нет":
        await update.message.reply_text(
            f"✅ <b>Новых задач не добавлено.</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📅 <b>План на день остаётся:</b> {context.user_data['daily_plan']} задач.",
            parse_mode="HTML",
        )
        return ConversationHandler.END

    lines = message_text.split("\n")
    is_strict_format = True
    for line in lines:
        parts = [part.strip() for part in line.split(",")]
        if len(parts) != 4:
            is_strict_format = False
            break

    if is_strict_format:
        for line in lines:
            parts = [part.strip() for part in line.split(",")]
            client, course, amount, payment_status = parts
            row_data = [client, course, amount, payment_status, "Нет", "bot"]
            sheet_manager.add_row(row_data)
            new_tasks.append(row_data)
    else:
        prompt = (
            """Ты помощник, преобразующий текст в JSON.
            Твоя задача — анализировать инструкцию и сделать с ней следующее:

            В запросе могут приходить различные названия колонок таблицы. То есть каждый человек может называть их по-разному.
            Вот примерные варианты того, как могут быть названы колонки в запросе на добавление новой записи:
            **Клиент** - [ОАО, ЗАО, ПАО, организация, физическое лицо, юридическое лицо, компания], а также все грамматические формы этих слов в русском языке
            **Курс** - [наш продукт, продукт], а также все грамматические формы этих слов в русском языке
            **Сумма** - [стоимость, стоимость курсов, цена, ценник, цена курса, цена курсов, прайс]. Также если в запросе пришли фразы по типу [курсы стоят, по цене, стоимостью], а дальше стоят цифры, то следует расценивать это как данные для графы "сумма"
            **Статус оплаты** - [подтверждение оплаты]. Если в запросе пришли фразы по типу [клиент оплатил, оплата подтверждена], то есть фразы, которые имеют значение подтверждения оплаты, то статус оплаты будет равен "Да"
            **Подтверждён ли заказ?** - При добавлении это поле всегда заполняется значением "Нет", если не написано в запросе иначе.

            Преобразуй следующую инструкцию в JSON для работы с таблицей.

            Верни результат в виде JSON **массива**, даже если задача одна. Каждый элемент массива — это объект с полями "клиент", "курс", "сумма", "статус оплаты", "Подтверждён ли заказ?".

            Пример твоего ответа:
            [
                {"клиент": "ООО Ромашка", "курс": "Фасад", "сумма": "10000", "статус оплаты": "Да", "Подтверждён ли заказ?": "Нет"},
                {"клиент": "ЗАО Клен", "курс": "Дизайн", "сумма": "15000", "статус оплаты": "Нет", "Подтверждён ли заказ?": "Нет"}
            ]

            Ответь **ТОЛЬКО** в формате JSON массива.\n\n"""
            f"Инструкция: {message_text}\n"
        )

        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Ты помощник, преобразующий текст в JSON-команды.",
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,
            temperature=0.0,
        )
        try:
            tasks_json_raw = response.choices[0].message.content.strip()
            tasks_json = json.loads(tasks_json_raw)

            if not isinstance(tasks_json, list):
                tasks_json = [tasks_json]

            for task in tasks_json:
                row_data = [
                    task.get("клиент", ""),
                    task.get("курс", ""),
                    task.get("сумма", ""),
                    task.get("статус оплаты", ""),
                    task.get("Подтверждён ли заказ?", "Нет"),
                    "bot",
                ]
                logging.info(
                    f"Добавление строки через LLM для менеджера {manager_id}: {row_data}"
                )
                sheet_manager.add_row(row_data)
                new_tasks.append(row_data)
        except (json.JSONDecodeError, AttributeError) as e:
            await update.message.reply_text(
                "❌ <b>Ошибка:</b> не удалось распознать задачи из текста. Попробуйте ещё раз в правильном формате.",
                parse_mode="HTML",
            )
            logging.error(f"Ошибка парсинга LLM ответа: {str(e)}")
            return ADD_TASKS

    new_tasks_count = len(new_tasks)
    context.user_data["daily_plan"] += new_tasks_count

    confirmation = (
        "✅ <b>Задачи успешно добавлены!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📋 <b>Добавлено {new_tasks_count} новых задач:</b>\n"
    )
    for task in new_tasks:
        confirmation += f"• {task[0]} | {task[1]} | {task[2]} | Оплата: {task[3]}\n"
    confirmation += (
        f"📅 <b>Обновлённый план на день:</b> {context.user_data['daily_plan']} задач."
    )

    await update.message.reply_text(confirmation, parse_mode="HTML")
    return ConversationHandler.END


__all__ = ["process_new_tasks"]
