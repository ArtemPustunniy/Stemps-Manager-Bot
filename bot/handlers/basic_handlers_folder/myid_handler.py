from telegram import Update
from telegram.ext import CallbackContext


async def myid(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    await update.message.reply_text(f"Ваш Telegram ID: {user_id}")


__all__ = ["myid"]
