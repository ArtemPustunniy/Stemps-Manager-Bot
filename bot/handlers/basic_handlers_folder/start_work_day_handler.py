from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler

from bot.handlers.basic_handlers import end_of_day_reminder
from bot.utils.role_manager import role_manager
from bot.utils.stats_manager import stats_manager
from google_sheets.manager import GoogleSheetManager
import logging
from bot.config.settings import OPENAI_API_KEY
from openai import AsyncOpenAI
from datetime import time
import pytz

openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

ADD_TASKS = 2


async def start_work_day(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    role = role_manager.get_role(user_id)
    if not role:
        await update.message.reply_text(
            "Вы не зарегистрированы. Обратитесь к директору."
        )
        return ConversationHandler.END

    if role_manager.is_active(user_id):
        await update.message.reply_text(
            "Бот уже работает для вас. Используйте /help для списка команд."
        )
        return ConversationHandler.END

    role_manager.set_active(user_id, True)

    manager_id = user_id
    spreadsheet_name = str(user_id)
    if role_manager.is_director(user_id) and context.args:
        try:
            manager_id = int(context.args[0])
            spreadsheet_name = str(manager_id)
        except ValueError:
            await update.message.reply_text("Ошибка: ID менеджера должен быть числом.")
            return ConversationHandler.END

    context.user_data["manager_id"] = manager_id
    context.user_data["spreadsheet_name"] = spreadsheet_name

    if role_manager.is_director(user_id):
        await update.message.reply_text(
            "👑 <b>Приветствую вас, директор!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌟 Удачного рабочего дня!\n",
            parse_mode="HTML",
        )
        return ConversationHandler.END

    yesterday_stats = stats_manager.get_yesterday_stats(manager_id)
    if not yesterday_stats:
        stats_text = (
            "📊 <b>Статистика за вчера:</b>\nЗа вчера вы не закрыли ни одного заказа."
        )
    else:
        stats_text = "📊 <b>Статистика закрытых заказов за вчера:</b>\n"
        for stat in yesterday_stats:
            client_name, course, contract_amount, timestamp = stat
            stats_text += (
                f"• {client_name} | {course} | {contract_amount} | {timestamp}\n"
            )

    sheet_manager = GoogleSheetManager(spreadsheet_name)
    all_rows = sheet_manager.sheet.get_all_values()[1:]
    unclosed_tasks = [
        row for row in all_rows if len(row) >= 5 and row[4].lower() == "нет"
    ]

    if not unclosed_tasks:
        unclosed_text = "✅ <b>Незакрытые задачи:</b>\nНезакрытых задач с вчера нет."
    else:
        unclosed_text = "✅ <b>Незакрытые задачи с вчера (нужно завершить):</b>\n"
        for task in unclosed_tasks:
            client_name = task[0] if len(task) > 0 else "Не указано"
            course = task[1] if len(task) > 1 else "Не указано"
            contract_amount = task[2] if len(task) > 2 else "Не указано"
            payment_status = task[3] if len(task) > 3 else "Не указано"
            unclosed_text += f"• {client_name} | {course} | {contract_amount} | Оплата: {payment_status}\n"

    completed_count = len(yesterday_stats)
    unclosed_count = len(unclosed_tasks)
    total_tasks_yesterday = completed_count + unclosed_count

    motivation_text = ""
    if total_tasks_yesterday > 0:
        unclosed_ratio = unclosed_count / total_tasks_yesterday
        if 0 < unclosed_ratio < 0.1:
            prompt = "Сгенерируй короткое креативное поощряющее сообщение для сотрудника, который вчера выполнил почти все задачи."
            response = await openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0.2,
            )
            ai_response = response.choices[0].message.content.strip()
            motivation_text = f"\n🎉 <b>Мотивация:</b>\n{ai_response}\n"
        elif unclosed_ratio == 0:
            prompt = "Сгенерируй короткое креативное поощряющее сообщение для сотрудника, который вчера выполнил вообще все задачи."
            response = await openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0.2,
            )
            ai_response = response.choices[0].message.content.strip()
            motivation_text = f"\n🎉 <b>Мотивация:</b>\n{ai_response}\n"
        elif unclosed_ratio > 0.1:
            motivation_text = (
                "\n🎉 <b>Мотивация:</b>\n"
                "Сегодня твой день, чтобы сиять! Осталось немного задач с вчера — "
                "вперёд к новым вершинам, ты всё сможешь!\n"
            )

    daily_plan = unclosed_count
    context.user_data["daily_plan"] = daily_plan
    context.user_data["completed_today"] = 0
    context.user_data["last_milestone"] = 0

    moscow_tz = pytz.timezone("Europe/Moscow")
    reminder_time = time(18, 45, tzinfo=moscow_tz)
    context.job_queue.run_daily(
        end_of_day_reminder,
        reminder_time,
        data=user_id,
        name=f"end_of_day_reminder_{user_id}",
    )
    logging.info(f"Ежедневное напоминание запланировано для {user_id} на 19:34 МСК")

    welcome_message = (
        "✅ <b>Бот включён!</b> Теперь вы можете использовать все команды.\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{stats_text}\n"
        f"{unclosed_text}\n"
        f"📅 <b>Текущий план на день:</b> {daily_plan} задач.\n"
        f"{motivation_text}"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📝 <b>Введите новые задачи на сегодня:</b>\n"
        "• В формате: <code>Клиент1, Курс1, Сумма1, Статус оплаты1</code>\n"
        "• Или опишите текстом (например, 'Добавить ООО Верба на курс Чёрный за 10000 с оплатой'),\n"
        "• Или напишите <code>'нет'</code>, если новых задач нет."
    )
    await update.message.reply_text(welcome_message, parse_mode="HTML")
    return ADD_TASKS


__all__ = ["start_work_day"]
