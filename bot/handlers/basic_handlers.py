import sqlite3

from telegram import Update
from telegram.ext import CallbackContext
from bot.utils.role_manager import role_manager
from bot.utils.stats_manager import stats_manager
from google_sheets.manager import GoogleSheetManager
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

    if role_manager.is_active(user_id):
        await update.message.reply_text("Бот уже работает для вас. Используйте /help для списка команд.")
        return

    role_manager.set_active(user_id, True)

    manager_id = user_id
    if role_manager.is_director(user_id) and context.args:
        try:
            manager_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("Ошибка: ID менеджера должен быть числом.")
            return

    yesterday_stats = stats_manager.get_yesterday_stats(manager_id)
    if not yesterday_stats:
        stats_text = "За вчера вы не закрыли ни одного заказа."
    else:
        stats_text = "Статистика закрытых заказов за вчера:\n"
        for stat in yesterday_stats:
            client_name, course, contract_amount, timestamp = stat
            stats_text += f"- {client_name} | {course} | {contract_amount} | {timestamp}\n"

    await update.message.reply_text(f"✅ Бот включён. Теперь вы можете использовать все команды.\n\n{stats_text}")


async def finish_work_day(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    role = role_manager.get_role(user_id)
    if not role:
        await update.message.reply_text("Вы не зарегистрированы. Обратитесь к директору.")
        return

    if not role_manager.is_active(user_id):
        await update.message.reply_text("Бот уже отключён для вас.")
        return

    # Если это менеджер, отправляем сводку директору
    if role_manager.is_manager(user_id):
        manager_id = user_id
        spreadsheet_name = str(manager_id)

        # Получаем закрытые заказы за сегодня
        today_stats = stats_manager.get_today_stats(manager_id)
        closed_count = len(today_stats)

        # Получаем незакрытые заказы из таблицы
        sheet_manager = GoogleSheetManager(spreadsheet_name)
        all_rows = sheet_manager.sheet.get_all_values()[1:]  # Пропускаем заголовок
        unclosed_count = sum(1 for row in all_rows if len(row) >= 5 and row[4].lower() == "нет")

        # Формируем сводку
        summary = f"Сводка по менеджеру {manager_id} за сегодня:\n"
        summary += f"Закрыто сделок: {closed_count}\n"
        if closed_count > 0:
            summary += "Подробности закрытых сделок:\n"
            for stat in today_stats:
                client_name, course, contract_amount, timestamp = stat
                summary += f"- {client_name} | {course} | {contract_amount} | {timestamp}\n"
        summary += f"Незакрытых сделок: {unclosed_count}"

        # Находим ID директора
        with sqlite3.connect("users.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT telegram_id FROM users WHERE role = 'director' LIMIT 1")
            director_id = cursor.fetchone()
            await update.message.reply_text("Директору будет отправлена сводка")
            if director_id:
                director_id = director_id[0]
                await context.bot.send_message(chat_id=director_id, text=summary)
            else:
                logging.warning("Директор не найден в базе данных.")

    # Отключаем бота для пользователя
    role_manager.set_active(user_id, False)
    await update.message.reply_text("✅ Бот отключён. До завтра!")
