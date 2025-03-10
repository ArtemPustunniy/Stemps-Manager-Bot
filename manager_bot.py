import logging
import os

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

load_dotenv()

CLIENT_NAME, COURSE, CONTRACT_AMOUNT, PAYMENT_STATUS, PLAN = range(5)

TOKEN = os.getenv("TOKEN")

sheet_manager = GoogleSheetManager("StempsManagement")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)


async def start(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        "Привет! Я бот для добавления данных в Google Таблицу.\nИспользуй команду /add, чтобы добавить запись."
    )


async def add(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("Введите название клиента (юрлицо):")
    return CLIENT_NAME


async def get_client_name(update: Update, context: CallbackContext) -> int:
    context.user_data["client_name"] = update.message.text
    await update.message.reply_text("Какой курс они покупают?")
    return COURSE


async def get_course(update: Update, context: CallbackContext) -> int:
    context.user_data["course"] = update.message.text
    await update.message.reply_text("Введите сумму договора для оплаты:")
    return CONTRACT_AMOUNT


async def get_contract_amount(update: Update, context: CallbackContext) -> int:
    context.user_data["contract_amount"] = update.message.text
    await update.message.reply_text("Оплата произведена? (Да/Нет)")
    return PAYMENT_STATUS


async def get_payment_status(update: Update, context: CallbackContext) -> int:
    context.user_data["payment_status"] = update.message.text
    await update.message.reply_text("Введите план недели/месяца:")
    return PLAN


async def get_plan(update: Update, context: CallbackContext) -> int:
    context.user_data["plan"] = update.message.text

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

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("add", add)],
        states={
            CLIENT_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_client_name)
            ],
            COURSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_course)],
            CONTRACT_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_contract_amount)
            ],
            PAYMENT_STATUS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, get_payment_status)
            ],
            PLAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_plan)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)

    print("🤖 Бот запущен!")
    app.run_polling()


if __name__ == "__main__":
    main()
