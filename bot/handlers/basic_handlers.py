from telegram import Update
from telegram.ext import CallbackContext
from bot.utils.role_manager import role_manager
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


async def start(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    role = role_manager.get_role(user_id)

    if role:
        if role_manager.is_active(user_id):
            await update.message.reply_text(f"Привет! Ваша роль: {role}\nДля списка команд используй /help.")
        else:
            await update.message.reply_text("Бот отключён для вас. Включите его командой /start_work_day.")
    else:
        await update.message.reply_text(
            "Привет! Вы не зарегистрированы в системе. Обратитесь к директору для получения роли.\n"
            "Узнайте свой ID с помощью /myid."
        )


async def help_command(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if not role_manager.is_active(user_id):
        await update.message.reply_text("Бот отключён для вас. Включите его командой /start_work_day.")
        return

    role = role_manager.get_role(user_id)
    if role_manager.is_director(user_id):
        help_text = (
            "Доступные команды для директора:\n"
            "/start - Начать работу с ботом\n"
            "/help - Показать список команд\n"
            "/add - Пошаговое добавление записи\n"
            "/ai_assistent - Добавление через текстовую инструкцию\n"
            "/manage_users - Управление пользователями\n"
            "/stats - Посмотреть статистику менеджера\n"
            "/myid - Узнать свой Telegram ID\n"
            "/start_work_day - Включить бота\n"
            "/finish_work_day - Отключить бота\n"
            "/cancel - Отменить текущую операцию"
        )
    elif role_manager.is_manager(user_id):
        help_text = (
            "Доступные команды для менеджера:\n"
            "/start - Начать работу с ботом\n"
            "/help - Показать список команд\n"
            "/add - Пошаговое добавление записи\n"
            "/ai_assistent - Добавление через текстовую инструкцию\n"
            "/myid - Узнать свой Telegram ID\n"
            "/start_work_day - Включить бота\n"
            "/finish_work_day - Отключить бота\n"
            "/cancel - Отменить текущую операцию"
        )
    else:
        help_text = (
            "Вы не зарегистрированы. Обратитесь к директору.\n"
            "/myid - Узнать свой Telegram ID\n"
            "/start_work_day - Включить бота (после регистрации)"
        )

    await update.message.reply_text(help_text)


async def myid(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    await update.message.reply_text(f"Ваш Telegram ID: {user_id}")


async def start_work_day(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    role = role_manager.get_role(user_id)
    if not role:
        await update.message.reply_text("Вы не зарегистрированы. Обратитесь к директору.")
        return

    role_manager.set_active(user_id, True)
    await update.message.reply_text("✅ Бот включён. Теперь вы можете использовать все команды.")


async def finish_work_day(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    role = role_manager.get_role(user_id)
    if not role:
        await update.message.reply_text("Вы не зарегистрированы. Обратитесь к директору.")
        return

    role_manager.set_active(user_id, False)
    await update.message.reply_text("✅ Бот отключён. До завтра!")