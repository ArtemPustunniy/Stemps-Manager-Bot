from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
from bot.config.settings import LLM_ADD
from bot.services.openai_service import get_commands_from_llm
from bot.utils.table_commands import execute_command
from bot.utils.role_manager import role_manager


async def llm_add(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    if not role_manager.is_active(user_id):
        await update.message.reply_text(
            "Бот отключён для вас. Включите его командой /start_work_day."
        )
        return ConversationHandler.END

    if not (role_manager.is_director(user_id) or role_manager.is_manager(user_id)):
        await update.message.reply_text(
            "У вас нет прав для добавления записей через AI."
        )
        return ConversationHandler.END

    if role_manager.is_manager(user_id):
        spreadsheet_name = str(user_id)
    elif role_manager.is_director(user_id) and context.args:
        spreadsheet_name = context.args[0]
    else:
        await update.message.reply_text(
            "Директор, укажите ID менеджера: /ai_assistent <telegram_id>"
        )
        return ConversationHandler.END

    context.user_data["spreadsheet_name"] = spreadsheet_name
    context.user_data["manager_id"] = (
        user_id if role_manager.is_manager(user_id) else int(spreadsheet_name)
    )
    await update.message.reply_text(
        "Отправьте текстовую инструкцию для добавления в таблицу:"
    )
    return LLM_ADD


async def process_llm_instruction(update: Update, context: CallbackContext) -> int:
    instruction = update.message.text
    commands = await get_commands_from_llm(instruction)

    if not commands:
        await update.message.reply_text(
            "Не удалось распознать инструкцию. Попробуйте еще раз."
        )
        return LLM_ADD

    results = [
        await execute_command(
            cmd,
            context.user_data["spreadsheet_name"],
            context.user_data["manager_id"],
            bot=context.bot,
            context=context,
        )
        for cmd in commands
    ]
    await update.message.reply_text("\n".join(results), parse_mode="HTML")
    return ConversationHandler.END
