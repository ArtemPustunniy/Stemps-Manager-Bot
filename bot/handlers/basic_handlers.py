# bot/handlers/basic_handlers.py
from telegram import Update
from telegram.ext import CallbackContext
from bot.utils.role_manager import role_manager


async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    role = role_manager.get_role(user_id)
    if role:
        await update.message.reply_text(f"Привет! Ваша роль: {role}\nДля списка команд используй /help.")
    else:
        await update.message.reply_text(
            "Привет! Вы не зарегистрированы в системе. Обратитесь к директору для получения роли.\n"
            "Узнайте свой ID с помощью /myid."
        )


async def help_command(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    role = role_manager.get_role(user_id)

    if role_manager.is_director(user_id):
        help_text = (
            "Доступные команды для директора:\n"
            "/start - Начать работу с ботом\n"
            "/help - Показать список команд\n"
            "/add - Пошаговое ручное добавление записи\n"
            "/AI_assistent - Добавить запись через текстовую инструкцию\n"
            "/manage_users - Управление пользователями\n"
            "/myid - Узнать свой Telegram ID\n"
            "/cancel - Отменить текущую операцию"
        )
    elif role_manager.is_manager(user_id):
        help_text = (
            "Доступные команды для менеджера:\n"
            "/start - Начать работу с ботом\n"
            "/help - Показать список команд\n"
            "/add - Пошаговое ручное добавление записи\n"
            "/AI_assistent - Добавить запись через текстовую инструкцию\n"
            "/myid - Узнать свой Telegram ID\n"
            "/cancel - Отменить текущую операцию"
        )
    else:
        help_text = (
            "Вы не зарегистрированы. Обратитесь к директору.\n"
            "/myid - Узнать свой Telegram ID"
        )

    await update.message.reply_text(help_text)


async def myid(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    await update.message.reply_text(f"Ваш Telegram ID: {user_id}")
