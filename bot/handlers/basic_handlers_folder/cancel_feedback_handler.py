from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
from bot.utils.role_manager import role_manager


async def cancel_feedback(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    role_manager.set_active(user_id, False)
    await update.message.reply_text("❌ Запрос фидбека отменён. Бот отключён.")
    return ConversationHandler.END


__all__ = ["cancel_feedback"]
