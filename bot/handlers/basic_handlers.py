import sqlite3

from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
from bot.utils.role_manager import role_manager
from bot.utils.stats_manager import stats_manager
from google_sheets.manager import GoogleSheetManager
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Состояния для ConversationHandler
FEEDBACK = 1


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
    spreadsheet_name = str(user_id)  # По умолчанию используем таблицу текущего пользователя
    if role_manager.is_director(user_id) and context.args:
        try:
            manager_id = int(context.args[0])
            spreadsheet_name = str(manager_id)  # Директор смотрит таблицу менеджера
        except ValueError:
            await update.message.reply_text("Ошибка: ID менеджера должен быть числом.")
            return

    # Получаем статистику закрытых заказов за вчера
    yesterday_stats = stats_manager.get_yesterday_stats(manager_id)
    if not yesterday_stats:
        stats_text = "За вчера вы не закрыли ни одного заказа."
    else:
        stats_text = "Статистика закрытых заказов за вчера:\n"
        for stat in yesterday_stats:
            client_name, course, contract_amount, timestamp = stat
            stats_text += f"- {client_name} | {course} | {contract_amount} | {timestamp}\n"

    # Получаем незакрытые задачи из таблицы
    sheet_manager = GoogleSheetManager(spreadsheet_name)
    all_rows = sheet_manager.sheet.get_all_values()[1:]  # Пропускаем заголовок
    unclosed_tasks = [row for row in all_rows if len(row) >= 5 and row[4].lower() == "нет"]

    if not unclosed_tasks:
        unclosed_text = "Незакрытых задач с вчера нет."
    else:
        unclosed_text = "Незакрытые задачи с вчера (нужно завершить):\n"
        for task in unclosed_tasks:
            client_name, course, contract_amount, payment_status, _ = task
            unclosed_text += f"- {client_name} | {course} | {contract_amount} | Оплата: {payment_status}\n"

    # Формируем итоговое сообщение
    welcome_message = (
        f"✅ Бот включён. Теперь вы можете использовать все команды.\n\n"
        f"{stats_text}\n\n"
        f"{unclosed_text}"
    )
    await update.message.reply_text(welcome_message)


async def finish_work_day(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    role = role_manager.get_role(user_id)
    if not role:
        await update.message.reply_text("Вы не зарегистрированы. Обратитесь к директору.")
        return ConversationHandler.END

    if not role_manager.is_active(user_id):
        await update.message.reply_text("Бот уже отключён для вас.")
        return ConversationHandler.END

    if role_manager.is_manager(user_id):
        manager_id = user_id
        spreadsheet_name = str(manager_id)

        # Удаляем подтверждённые заказы из таблицы без уведомлений
        sheet_manager = GoogleSheetManager(spreadsheet_name)
        all_rows = sheet_manager.sheet.get_all_values()[1:]  # Пропускаем заголовок
        deleted_count = 0
        for i, row in enumerate(all_rows[::-1]):  # Обратный порядок, чтобы индексы не смещались
            if len(row) >= 5 and row[4].lower() == "да":
                row_index = len(all_rows) - i + 1  # Индекс строки в таблице (с учётом заголовка)
                sheet_manager.delete_row(row_index)  # Удаляем напрямую
                deleted_count += 1

        # Получаем закрытые заказы за сегодня
        today_stats = stats_manager.get_today_stats(manager_id)
        closed_count = len(today_stats)

        # Получаем незакрытые заказы из таблицы (после удаления)
        all_rows = sheet_manager.sheet.get_all_values()[1:]  # Обновляем после удаления
        unclosed_count = sum(1 for row in all_rows if len(row) >= 5 and row[4].lower() == "нет")

        # Сохраняем данные в context.user_data для использования в фидбеке
        context.user_data["manager_id"] = manager_id
        context.user_data["closed_count"] = closed_count
        context.user_data["today_stats"] = today_stats
        context.user_data["unclosed_count"] = unclosed_count
        context.user_data["deleted_count"] = deleted_count

        # Запрашиваем фидбек
        await update.message.reply_text(
            "✅ Подтверждённые заказы удалены из таблицы.\n"
            "Пожалуйста, напишите краткий фидбек по рабочему дню: что получилось, что не получилось."
        )
        return FEEDBACK

    # Для директора просто отключаем бота
    role_manager.set_active(user_id, False)
    await update.message.reply_text("✅ Бот отключён. До завтра!")
    return ConversationHandler.END


async def process_feedback(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    feedback = update.message.text

    # Формируем сводку с фидбеком
    manager_id = context.user_data["manager_id"]
    closed_count = context.user_data["closed_count"]
    today_stats = context.user_data["today_stats"]
    unclosed_count = context.user_data["unclosed_count"]
    deleted_count = context.user_data["deleted_count"]

    summary = f"Сводка по менеджеру {manager_id} за сегодня:\n"
    summary += f"Закрыто сделок: {closed_count}\n"
    if closed_count > 0:
        summary += "Подробности закрытых сделок:\n"
        for stat in today_stats:
            client_name, course, contract_amount, timestamp = stat
            summary += f"- {client_name} | {course} | {contract_amount} | {timestamp}\n"
    summary += f"Незакрытых сделок: {unclosed_count}\n"
    summary += f"Удалено подтверждённых записей из таблицы: {deleted_count}\n"
    summary += f"Фидбек менеджера:\n{feedback}"

    # Находим ID директора и отправляем сводку
    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT telegram_id FROM users WHERE role = 'director' LIMIT 1")
        director_id = cursor.fetchone()
        if director_id:
            director_id = director_id[0]
            await context.bot.send_message(chat_id=director_id, text=summary)
        else:
            logging.warning("Директор не найден в базе данных.")

    # Отключаем бота для пользователя
    role_manager.set_active(user_id, False)
    await update.message.reply_text("✅ Бот отключён. Спасибо за фидбек! До завтра!")
    return ConversationHandler.END


async def cancel_feedback(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    role_manager.set_active(user_id, False)
    await update.message.reply_text("❌ Запрос фидбека отменён. Бот отключён.")
    return ConversationHandler.END