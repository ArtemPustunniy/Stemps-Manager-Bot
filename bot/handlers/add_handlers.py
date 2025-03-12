from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
from bot.config.settings import CLIENT_NAME, COURSE, CONTRACT_AMOUNT, PAYMENT_STATUS, PLAN
from bot.utils.role_manager import role_manager


async def add(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    if not (role_manager.is_director(user_id) or role_manager.is_manager(user_id)):
        await update.message.reply_text("У вас нет прав для добавления записей.")
        return ConversationHandler.END

    context.user_data.clear()
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
    await update.message.reply_text("Подтверждён ли заказ?")
    return PLAN


async def get_plan(update: Update, context: CallbackContext) -> int:
    from google_sheets.manager import GoogleSheetManager
    sheet_manager = GoogleSheetManager("StempsManagement")

    context.user_data["order_status"] = update.message.text
    new_row = [
        context.user_data["client_name"],
        context.user_data["course"],
        context.user_data["contract_amount"],
        context.user_data["payment_status"],
        context.user_data["order_status"],
    ]
    sheet_manager.add_row(new_row)
    await update.message.reply_text("✅ Данные успешно добавлены в таблицу!")
    return ConversationHandler.END


async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("❌ Добавление данных отменено.")
    return ConversationHandler.END