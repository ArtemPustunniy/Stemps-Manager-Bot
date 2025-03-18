from telegram import Update
from telegram.ext import CallbackContext
from bot.utils.role_manager import role_manager


async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    role = role_manager.get_role(user_id)

    if role:
        if role_manager.is_active(user_id):
            await update.message.reply_text(
                f"Привет! Ваша роль: {role}\nДля списка команд используй /help."
            )
        else:
            await update.message.reply_text(
                "Бот отключён для вас. Включите его командой /start_work_day."
            )
    else:
        await update.message.reply_text(
            "Привет! Вы не зарегистрированы в системе. Обратитесь к директору для получения роли.\n"
            "Узнайте свой ID с помощью /myid."
        )


__all__ = ["start"]
