import sqlite3
from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler, MessageHandler, filters
from bot.utils.role_manager import role_manager
from bot.utils.stats_manager import stats_manager
from google_sheets.manager import GoogleSheetManager
import logging
from bot.config.settings import OPENAI_API_KEY
from openai import AsyncOpenAI

openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Состояния для ConversationHandler
FEEDBACK = 1
ADD_TASKS = 2


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


async def start_work_day(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    role = role_manager.get_role(user_id)
    if not role:
        await update.message.reply_text("Вы не зарегистрированы. Обратитесь к директору.")
        return ConversationHandler.END

    if role_manager.is_active(user_id):
        await update.message.reply_text("Бот уже работает для вас. Используйте /help для списка команд.")
        return ConversationHandler.END

    role_manager.set_active(user_id, True)

    manager_id = user_id
    spreadsheet_name = str(user_id)
    if role_manager.is_director(user_id) and context.args:
        try:
            manager_id = int(context.args[0])
            spreadsheet_name = str(manager_id)
        except ValueError:
            await update.message.reply_text("Ошибка: ID менеджера должен быть числом.")
            return ConversationHandler.END

    # Сохраняем данные в context.user_data
    context.user_data["manager_id"] = manager_id
    context.user_data["spreadsheet_name"] = spreadsheet_name

    # Получаем статистику закрытых заказов за вчера
    yesterday_stats = stats_manager.get_yesterday_stats(manager_id)
    if not yesterday_stats:
        stats_text = "За вчера вы не закрыли ни одного заказа."
    else:
        stats_text = "Статистика закрытых заказов за вчера:\n"
        for stat in yesterday_stats:
            client_name, course, contract_amount, timestamp = stat
            stats_text += f"- {client_name} | {course} | {contract_amount} | {timestamp}\n"

    # Получаем незакрытые задачи из таблицы — это будет начальный план на день
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

    # Вычисляем отношение невыполненных задач к выполненным за вчера
    completed_count = len(yesterday_stats)
    unclosed_count = len(unclosed_tasks)
    total_tasks_yesterday = completed_count + unclosed_count

    motivation_text = ""
    if total_tasks_yesterday > 0:
        unclosed_ratio = unclosed_count / total_tasks_yesterday
        if 0 < unclosed_ratio < 0.1:
            prompt = "Сгенерируй короткое креативное поощряющее сообщение для сотрудника, который вчера выполнил почти все задачи."
            response = await openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0.2
            )
            ai_response = response.choices[0].message.content.strip()
            motivation_text = f"\n{ai_response}\n"
        elif unclosed_ratio == 0:
            prompt = "Сгенерируй короткое креативное поощряющее сообщение для сотрудника, который вчера выполнил вообще все задачи."
            response = await openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0.2
            )
            ai_response = response.choices[0].message.content.strip()
            motivation_text = f"\n{ai_response}\n"
        elif unclosed_ratio > 0.1:
            motivation_text = (
                "\nСегодня твой день, чтобы сиять! Осталось немного задач с вчера — "
                "вперёд к новым вершинам, ты всё сможешь!\n"
            )

    # Устанавливаем начальный план на день и инициализируем прогресс
    daily_plan = unclosed_count
    context.user_data["daily_plan"] = daily_plan
    context.user_data["completed_today"] = 0
    context.user_data["last_milestone"] = 0

    # Формируем итоговое сообщение и запрашиваем новые задачи
    welcome_message = (
        f"✅ Бот включён. Теперь вы можете использовать все команды.\n\n"
        f"{stats_text}\n\n"
        f"{unclosed_text}"
        f"Текущий план на день: {daily_plan} задач.\n"
        f"{motivation_text}"
        "\nПожалуйста, введите новые задачи на сегодня в формате:\n"
        "Клиент1, Курс1, Сумма1, Статус оплаты1\n"
        "Клиент2, Курс2, Сумма2, Статус оплаты2\n"
        "(или напишите 'нет', если новых задач нет)"
    )
    await update.message.reply_text(welcome_message)
    return ADD_TASKS


async def process_new_tasks(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    message_text = update.message.text.strip()

    spreadsheet_name = context.user_data.get("spreadsheet_name")
    manager_id = context.user_data.get("manager_id")
    if not spreadsheet_name or not manager_id:
        await update.message.reply_text("Ошибка: данные менеджера не найдены. Начните заново с /start_work_day.")
        return ConversationHandler.END

    sheet_manager = GoogleSheetManager(spreadsheet_name)
    new_tasks = []

    if message_text.lower() == "нет":
        await update.message.reply_text(f"Новых задач не добавлено. План на день остаётся: {context.user_data['daily_plan']} задач.")
        return ConversationHandler.END

    # Парсим задачи из сообщения
    lines = message_text.split("\n")
    for line in lines:
        parts = [part.strip() for part in line.split(",")]
        if len(parts) == 4:  # Ожидаем клиент, курс, сумма, статус оплаты
            client, course, amount, payment_status = parts
            row_data = [client, course, amount, payment_status, "Нет"]  # По умолчанию "Подтверждён ли заказ?" = Нет
            sheet_manager.add_row(row_data)
            new_tasks.append(row_data)
        else:
            await update.message.reply_text(f"Ошибка в формате строки: '{line}'. Ожидается: Клиент, Курс, Сумма, Статус оплаты.")
            return ADD_TASKS  # Возвращаем пользователя к вводу

    # Обновляем план на день
    new_tasks_count = len(new_tasks)
    context.user_data["daily_plan"] += new_tasks_count

    # Формируем подтверждение
    confirmation = f"Добавлено {new_tasks_count} новых задач:\n"
    for task in new_tasks:
        confirmation += f"- {task[0]} | {task[1]} | {task[2]} | Оплата: {task[3]}\n"
    confirmation += f"Обновлённый план на день: {context.user_data['daily_plan']} задач."

    await update.message.reply_text(confirmation)
    return ConversationHandler.END


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

        sheet_manager = GoogleSheetManager(spreadsheet_name)
        all_rows = sheet_manager.sheet.get_all_values()[1:]
        deleted_count = 0
        for i, row in enumerate(all_rows[::-1]):
            if len(row) >= 5 and row[4].lower() == "да":
                row_index = len(all_rows) - i + 1
                sheet_manager.delete_row(row_index)
                deleted_count += 1

        today_stats = stats_manager.get_today_stats(manager_id)
        closed_count = len(today_stats)

        all_rows = sheet_manager.sheet.get_all_values()[1:]
        unclosed_count = sum(1 for row in all_rows if len(row) >= 5 and row[4].lower() == "нет")

        context.user_data["manager_id"] = manager_id
        context.user_data["closed_count"] = closed_count
        context.user_data["today_stats"] = today_stats
        context.user_data["unclosed_count"] = unclosed_count
        context.user_data["deleted_count"] = deleted_count

        await update.message.reply_text(
            "✅ Подтверждённые заказы удалены из таблицы.\n"
            "Пожалуйста, напишите краткий фидбек по рабочему дню: что получилось, что не получилось."
        )
        return FEEDBACK

    role_manager.set_active(user_id, False)
    await update.message.reply_text("✅ Бот отключён. До завтра!")
    return ConversationHandler.END


async def process_feedback(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    feedback = update.message.text

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

    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT telegram_id FROM users WHERE role = 'director' LIMIT 1")
        director_id = cursor.fetchone()
        if director_id:
            director_id = director_id[0]
            await context.bot.send_message(chat_id=director_id, text=summary)
        else:
            logging.warning("Директор не найден в базе данных.")

    role_manager.set_active(user_id, False)
    await update.message.reply_text("✅ Бот отключён. Спасибо за фидбек! До завтра!")
    return ConversationHandler.END


async def cancel_feedback(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    role_manager.set_active(user_id, False)
    await update.message.reply_text("❌ Запрос фидбека отменён. Бот отключён.")
    return ConversationHandler.END