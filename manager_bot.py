import logging
import os
import json
from typing import List, Dict
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    CallbackContext,
)
from google_sheets import GoogleSheetManager
from openai import AsyncOpenAI

load_dotenv()

CLIENT_NAME, COURSE, CONTRACT_AMOUNT, PAYMENT_STATUS, PLAN, LLM_ADD = range(6)

TOKEN = os.getenv("TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

sheet_manager = GoogleSheetManager("StempsManagement")
openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


class TableCommands:
    ADD_ROW = "add_row"
    UPDATE_CELL = "update_cell"
    DELETE_ROW = "delete_row"


async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "Привет! Я бот для работы с Google Таблицей.\n"
        "Для списка команд используй /help."
    )


async def help_command(update: Update, context: CallbackContext) -> None:
    help_text = (
        "Доступные команды:\n"
        "/start - Начать работу с ботом\n"
        "/help - Показать список команд\n"
        "/add - Пошаговое ручное добавление записи\n"
        "/AI_assistent - Добавить запись через текстовую инструкцию (обрабатывается LLM)\n"
        "/cancel - Отменить текущую операцию"
    )
    await update.message.reply_text(help_text)


async def llm_add(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Отправьте текстовую инструкцию для добавления в таблицу:")
    return LLM_ADD


async def process_llm_instruction(update: Update, context: CallbackContext) -> int:
    instruction = update.message.text
    logging.info(f"Получена инструкция для LLM: {instruction}")

    commands = await get_commands_from_llm(instruction)

    if not commands:
        await update.message.reply_text("Не удалось распознать инструкцию. Попробуйте еще раз.")
        return LLM_ADD

    results = []
    for cmd in commands:
        result = await execute_command(cmd)
        results.append(result)

    await update.message.reply_text("\n".join(results))
    return ConversationHandler.END


async def get_commands_from_llm(instruction: str) -> List[Dict]:
    try:
        prompt = (
            """Ты помощник, преобразующий текст в JSON-команды.
            Твоя задача — анализировать инструкцию и сделать с ней следующее:
            
            В запросе могут приходить различные названия колонок таблицы. То есть каждый человек может наывать их по-разному.
            Вот примерные варианты того, как могут быть названы колонки в запросе на добавление новой записи:
            **Клиент** - [ОАО, ЗАО, ПАО, организация, физическое лицо, юридическое лицо, компания], а так же все грамматические формы этих слов в русском языке
            **Курс** - [наш продукт, продукт], а так же все грамматические формы этих слов в русском языке
            **Сумма** - [стоимость, стоимость курсов, цена, ценник, цена курса, цена курсов, прайс]. Так же если в запросе пришли фразы по типу [курсы стоят, по цене, стоимостью], а дальше стоят цифры, то следует расценивать это как данные для графы "сумма"
            **Статус оплаты** - [подтверждение оплаты]. Если в запросе пришли фразы по типу [клиент оплатил, оплата подтвержена], то есть фразы, которые имеют значение подтверждения оплаты, то статус оплаты будет равен "Да"
            
            Вот примерные варианты того, как могут быть названы колонки в запросе на добавление на обновление ячейки:
            **Клиент** - [ОАО, ЗАО, ПАО, организация, физическое лицо, юридическое лицо, компания], а так же все грамматические формы этих слов в русском языке
            **Столбец** - Этот столбец заполняется на основании того, что человеку нужно поменять. 
            
            Вот примерные варианты того, как могут быть названы колонки в запросе на удаление записи:
            **Клиент** - [ОАО, ЗАО, ПАО, организация, физическое лицо, юридическое лицо, компания], а так же все грамматические формы этих слов в русском языке
            **Курс** - [наш продукт, продукт], а так же все грамматические формы этих слов в русском языке
            
            Преобразуй следующую инструкцию в список JSON-команд для работы с таблицей.
            Доступные команды: add_row, update_cell, delete_row.
            
            **В запросе на добавление новой записи обязательно будет присутствовать ключевое слово, связанное с добавлением, например, добавь, добавить и так далее**
            **В запросе на обновление ячейки обязательно будет присутствовать ключевое слово, связанное с обновлением, например, обнови, обновить, изменить значение и так далее**
            **В запросе на удаление записи обязательно будет присутствовать ключевое слово, связанное с удали, например, удали, удалить, уничтожить, убрать из базы и так далее**
            
            Каждая команда должна иметь структуру: {"command": "<команда>", "parameters": {"ключ": "значение", ...}}.
            Верни только чистый JSON без дополнительного текста.\n\n"""
            f"Инструкция: {instruction}\n"
            """Примеры твоего ответа в JSON:
            Для добавления записи:
            {"command": "add_row", "parameters": {"клиент": "ООО Ромашка", "курс": "Фасад", "сумма": "10000", "статус оплаты": "Да", "план": "100000"}}
            Для обновления ячейки:
            {"command": "update_cell", "parameters": {"клиент": "ООО Ромашка", "столбец": "сумма", "значение": "20000"}}
            Для удаления строки:
            {"command": "delete_row", "parameters": {"клиент": "ООО Ромашка", "курс": "Фасад"}}
            Ответь **ТОЛЬКО** в формате JSON."""
        )

        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты помощник, преобразующий текст в JSON-команды."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.0
        )

        commands_text = response.choices[0].message.content.strip()
        commands = json.loads(commands_text)
        print(commands)
        return [commands] if isinstance(commands, dict) else commands

    except json.JSONDecodeError as e:
        logging.error(f"Ошибка парсинга JSON от OpenAI: {e}")
        return []
    except Exception as e:
        logging.error(f"Ошибка при запросе к OpenAI: {e}")
        return []


async def execute_command(command: Dict) -> str:
    try:
        cmd = command.get("command")
        params = command.get("parameters", {})

        if cmd == TableCommands.ADD_ROW:
            row_data = [
                params.get("клиент", ""),
                params.get("курс", ""),
                params.get("сумма", ""),
                params.get("статус оплаты", ""),
                params.get("план", "")
            ]
            sheet_manager.add_row(row_data)
            return f"✅ Добавлена строка: {row_data}"

        elif cmd == TableCommands.UPDATE_CELL:
            client = params.get("клиент", "")
            column = params.get("столбец", "")
            value = params.get("значение", "")  # Новое значение из параметров

            # Ищем строку по клиенту
            row_index = sheet_manager.find_row(client)
            if not row_index:
                return f"❌ Клиент {client} не найден"

            # Определяем индекс столбца
            column_index = {"курс": 2, "сумма": 3, "статус оплаты": 4}.get(column)
            if not column_index:
                return f"❌ Неизвестный столбец: {column}"

            sheet_manager.update_cell(row_index, column_index, value)
            return f"✅ Обновлена ячейка ({row_index}, {column}) для клиента {client}: {value}"

        elif cmd == TableCommands.DELETE_ROW:
            client = params.get("клиент", "")
            course = params.get("курс", "")

            # Ищем строку по клиенту и курсу
            row_index = sheet_manager.find_row(client, course)
            if not row_index:
                return f"❌ Клиент {client} с курсом {course} не найден"

            sheet_manager.delete_row(row_index)
            return f"✅ Удалена строка {row_index} для клиента {client}, курс {course}"

        else:
            return f"❌ Неизвестная команда: {cmd}"

    except Exception as e:
        return f"❌ Ошибка выполнения команды: {str(e)}"


async def add(update: Update, context: CallbackContext) -> int:
    context.user_data.clear()
    await update.message.reply_text("Введите название клиента (юрлицо):")
    return CLIENT_NAME


async def get_client_name(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    logging.info(f"Получено название клиента: {text}")

    context.user_data["client_name"] = text
    await update.message.reply_text("Какой курс они покупают?")
    return COURSE


async def get_course(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    logging.info(f"Получен курс: {text}")

    context.user_data["course"] = text
    await update.message.reply_text("Введите сумму договора для оплаты:")
    return CONTRACT_AMOUNT


async def get_contract_amount(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    logging.info(f"Получена сумма договора: {text}")

    context.user_data["contract_amount"] = text
    await update.message.reply_text("Оплата произведена? (Да/Нет)")
    return PAYMENT_STATUS


async def get_payment_status(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    logging.info(f"Получен статус оплаты: {text}")

    context.user_data["payment_status"] = text
    await update.message.reply_text("Введите план недели/месяца:")
    return PLAN


async def get_plan(update: Update, context: CallbackContext) -> int:
    text = update.message.text
    logging.info(f"Получен план: {text}")

    context.user_data["plan"] = text

    new_row = [
        context.user_data["client_name"],
        context.user_data["course"],
        context.user_data["contract_amount"],
        context.user_data["payment_status"],
        context.user_data["plan"],
    ]
    sheet_manager.add_row(new_row)

    await update.message.reply_text("✅ Данные успешно добавлены в таблицу!")
    return ConversationHandler.END


async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("❌ Добавление данных отменено.")
    return ConversationHandler.END


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("add", add),
            CommandHandler("AI_assistent", llm_add)
        ],
        states={
            CLIENT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_client_name)],
            COURSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_course)],
            CONTRACT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_contract_amount)],
            PAYMENT_STATUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_payment_status)],
            PLAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_plan)],
            LLM_ADD: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_llm_instruction)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)

    print("🤖 Бот запущен!")
    app.run_polling()


if __name__ == "__main__":
    main()
