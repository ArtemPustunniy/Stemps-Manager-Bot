from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
from bot.config.settings import LLM_ADD
from bot.services.openai_service import get_commands_from_llm
from bot.utils.table_commands import execute_command
from bot.utils.role_manager import role_manager


async def llm_add(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    if not (role_manager.is_director(user_id) or role_manager.is_manager(user_id)):
        await update.message.reply_text("У вас нет прав для добавления записей через AI.")
        return ConversationHandler.END

    await update.message.reply_text("Отправьте текстовую инструкцию для добавления в таблицу:")
    return LLM_ADD


async def process_llm_instruction(update: Update, context: CallbackContext) -> int:
    instruction = update.message.text
    commands = await get_commands_from_llm(instruction)

    if not commands:
        await update.message.reply_text("Не удалось распознать инструкцию. Попробуйте еще раз.")
        return LLM_ADD

    results = [await execute_command(cmd) for cmd in commands]
    await update.message.reply_text("\n".join(results))
    return ConversationHandler.END