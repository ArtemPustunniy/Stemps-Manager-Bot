from telegram import Update
from telegram.ext import CallbackContext, CommandHandler
from bot.utils.role_manager import role_manager
from bot.config.settings import ROLES


async def manage_users(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if not role_manager.is_director(user_id):
        await update.message.reply_text("Эта команда доступна только директору.")
        return

    try:
        args = context.args
        if len(args) != 2:
            await update.message.reply_text("Использование: /manage_users <telegram_id> <role>\nРоли: director, manager")
            return

        target_id = int(args[0])
        role = args[1].lower()
        if role not in [ROLES["DIRECTOR"], ROLES["MANAGER"]]:
            await update.message.reply_text("Неверная роль. Доступные роли: director, manager")
            return

        role_manager.add_user(target_id, role)
        await update.message.reply_text(f"Пользователь {target_id} добавлен с ролью {role}.")
    except ValueError:
        await update.message.reply_text("Telegram ID должен быть числом.")


def setup_handlers(application):
    application.add_handler(CommandHandler("manage_users", manage_users))