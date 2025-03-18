from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
from bot.config.settings import (
    CLIENT_NAME,
    COURSE,
    CONTRACT_AMOUNT,
    PAYMENT_STATUS,
    PLAN,
)
from bot.utils.role_manager import role_manager
from bot.utils.table_commands import execute_command


async def add(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    if not role_manager.is_active(user_id):
        await update.message.reply_text(
            "Бот отключён для вас. Включите его командой /start_work_day."
        )
        return ConversationHandler.END

    if not (role_manager.is_director(user_id) or role_manager.is_manager(user_id)):
        await update.message.reply_text("У вас нет прав для добавления записей.")
        return ConversationHandler.END

    if role_manager.is_manager(user_id):
        spreadsheet_name = str(user_id)
    elif role_manager.is_director(user_id):
        if context.args:
            spreadsheet_name = context.args[0]
        else:
            await update.message.reply_text(
                "Директор, укажите ID менеджера: /add <telegram_id>"
            )
            return ConversationHandler.END
    else:
        await update.message.reply_text("Неизвестная ошибка с ролями.")
        return ConversationHandler.END

    context.user_data["spreadsheet_name"] = spreadsheet_name
    context.user_data["manager_id"] = (
        user_id if role_manager.is_manager(user_id) else int(spreadsheet_name)
    )
    context.user_data.clear()
    context.user_data["spreadsheet_name"] = spreadsheet_name
    context.user_data["manager_id"] = (
        user_id if role_manager.is_manager(user_id) else int(spreadsheet_name)
    )
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
    await update.message.reply_text("Подтверждён ли заказ? (Да/Нет)")
    return PLAN


async def get_plan(update: Update, context: CallbackContext) -> int:
    if "spreadsheet_name" not in context.user_data:
        await update.message.reply_text(
            "Ошибка: не указана таблица для работы. Начните заново с /add."
        )
        return ConversationHandler.END

    order_status = update.message.text.lower() == "да"
    new_row = [
        context.user_data["client_name"],
        context.user_data["course"],
        context.user_data["contract_amount"],
        context.user_data["payment_status"],
        order_status and "Да" or "Нет",
    ]
    result = await execute_command(
        {
            "command": "add_row",
            "parameters": {
                "клиент": new_row[0],
                "курс": new_row[1],
                "сумма": new_row[2],
                "статус оплаты": new_row[3],
                "Подтверждён ли заказ?": new_row[4],
                "Автор изменений": "bot",
            },
        },
        context.user_data["spreadsheet_name"],
        context.user_data["manager_id"],
        bot=context.bot,
    )
    await update.message.reply_text(result, parse_mode="HTML")
    return ConversationHandler.END


async def cancel(update: Update, context: CallbackContext) -> int:
    await update.message.reply_text("❌ Добавление данных отменено.")
    return ConversationHandler.END
