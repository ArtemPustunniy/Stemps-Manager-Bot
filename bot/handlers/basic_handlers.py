import sqlite3
import json
from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler, MessageHandler, filters
from bot.utils.role_manager import role_manager
from bot.utils.stats_manager import stats_manager
from google_sheets.manager import GoogleSheetManager
import logging
from bot.config.settings import OPENAI_API_KEY
from openai import AsyncOpenAI
from datetime import datetime, time
import pytz

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
        await update.message.reply_text(
            "⚠️ *Бот отключён для вас\\. Включите его командой* `/start_work_day`\\.",
            parse_mode="MarkdownV2"
        )
        return

    role = role_manager.get_role(user_id)
    if role_manager.is_director(user_id):
        help_text = (
            "👑 *Команды для директора*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📋 *Основные команды:*\n"
            "• `/start` — Начать работу с ботом\n"
            "• `/help` — Показать список команд\n"
            "• `/myid` — Узнать свой Telegram ID\n"
            "• `/start_work_day` — Включить бота\n"
            "• `/finish_work_day` — Отключить бота\n"
            "• `/cancel` — Отменить текущую операцию\n"
            "\n📝 *Добавление записей:*\n"
            "• `/add` — Пошаговое добавление записи\n"
            "• `/ai_assistent` — Добавление через текстовую инструкцию\n"
            "\n📊 *Управление и статистика:*\n"
            "• `/manage_users` — Управление пользователями\n"
            "• `/stats` — Посмотреть статистику менеджера\n"
            "• `/today_revenue` — Статистика всех менеджеров\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 Используйте команды для эффективной работы\\!"
        )
    elif role_manager.is_manager(user_id):
        help_text = (
            "🧑‍💼 *Команды для менеджера*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📋 *Основные команды:*\n"
            "• `/start` — Начать работу с ботом\n"
            "• `/help` — Показать список команд\n"
            "• `/myid` — Узнать свой Telegram ID\n"
            "• `/start_work_day` — Включить бота\n"
            "• `/finish_work_day` — Отключить бота\n"
            "• `/cancel` — Отменить текущую операцию\n"
            "\n📝 *Добавление записей:*\n"
            "• `/add` — Пошаговое добавление записи\n"
            "• `/ai_assistent` — Добавление через текстовую инструкцию\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "💡 Выполняйте задачи и закрывайте заказы\\!"
        )
    else:
        help_text = (
            "🚫 *Вы не зарегистрированы*\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Обратитесь к директору для регистрации\\.\n"
            "📋 *Доступные команды:*\n"
            "• `/myid` — Узнать свой Telegram ID\n"
            "• `/start_work_day` — Включить бота \\(после регистрации\\)\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📞 Свяжитесь с директором для доступа\\!"
        )

    await update.message.reply_text(
        help_text,
        parse_mode="MarkdownV2"
    )


async def myid(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    await update.message.reply_text(f"Ваш Telegram ID: {user_id}")


async def end_of_day_reminder(context: CallbackContext) -> None:
    user_id = context.job.data
    if role_manager.is_active(user_id):
        await context.bot.send_message(
            chat_id=user_id,
            text=(
                "⏰ <b>Напоминание: до конца рабочего дня 15 минут!</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                "🕖 Текущее время: 19:00 МСК\n"
                "📋 Пора подвести итоги и подготовить отчёт.\n"
                "👉 Используйте команду <code>/finish_work_day</code>, чтобы завершить день и оставить фидбек.\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                "💡 Не забудьте завершить все задачи!"
            ),
            parse_mode="HTML"
        )


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

    context.user_data["manager_id"] = manager_id
    context.user_data["spreadsheet_name"] = spreadsheet_name

    if role_manager.is_director(user_id):
        await update.message.reply_text(
            "👑 <b>Приветствую вас, директор!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "🌟 Удачного рабочего дня!\n",
            parse_mode="HTML"
        )
        return ConversationHandler.END

    yesterday_stats = stats_manager.get_yesterday_stats(manager_id)
    if not yesterday_stats:
        stats_text = "📊 <b>Статистика за вчера:</b>\nЗа вчера вы не закрыли ни одного заказа."
    else:
        stats_text = "📊 <b>Статистика закрытых заказов за вчера:</b>\n"
        for stat in yesterday_stats:
            client_name, course, contract_amount, timestamp = stat
            stats_text += f"• {client_name} | {course} | {contract_amount} | {timestamp}\n"

    sheet_manager = GoogleSheetManager(spreadsheet_name)
    all_rows = sheet_manager.sheet.get_all_values()[1:]
    unclosed_tasks = [row for row in all_rows if len(row) >= 5 and row[4].lower() == "нет"]

    if not unclosed_tasks:
        unclosed_text = "✅ <b>Незакрытые задачи:</b>\nНезакрытых задач с вчера нет."
    else:
        unclosed_text = "✅ <b>Незакрытые задачи с вчера (нужно завершить):</b>\n"
        for task in unclosed_tasks:
            client_name = task[0] if len(task) > 0 else "Не указано"
            course = task[1] if len(task) > 1 else "Не указано"
            contract_amount = task[2] if len(task) > 2 else "Не указано"
            payment_status = task[3] if len(task) > 3 else "Не указано"
            unclosed_text += f"• {client_name} | {course} | {contract_amount} | Оплата: {payment_status}\n"

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
            motivation_text = f"\n🎉 <b>Мотивация:</b>\n{ai_response}\n"
        elif unclosed_ratio == 0:
            prompt = "Сгенерируй короткое креативное поощряющее сообщение для сотрудника, который вчера выполнил вообще все задачи."
            response = await openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0.2
            )
            ai_response = response.choices[0].message.content.strip()
            motivation_text = f"\n🎉 <b>Мотивация:</b>\n{ai_response}\n"
        elif unclosed_ratio > 0.1:
            motivation_text = (
                "\n🎉 <b>Мотивация:</b>\n"
                "Сегодня твой день, чтобы сиять! Осталось немного задач с вчера — "
                "вперёд к новым вершинам, ты всё сможешь!\n"
            )

    daily_plan = unclosed_count
    context.user_data["daily_plan"] = daily_plan
    context.user_data["completed_today"] = 0
    context.user_data["last_milestone"] = 0

    # Планируем ежедневное напоминание на 19:34 МСК
    moscow_tz = pytz.timezone("Europe/Moscow")
    reminder_time = time(21, 10, tzinfo=moscow_tz)
    context.job_queue.run_daily(
        end_of_day_reminder,
        reminder_time,
        data=user_id,
        name=f"end_of_day_reminder_{user_id}"
    )
    logging.info(f"Ежедневное напоминание запланировано для {user_id} на 19:34 МСК")

    welcome_message = (
        "✅ <b>Бот включён!</b> Теперь вы можете использовать все команды.\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{stats_text}\n"
        f"{unclosed_text}\n"
        f"📅 <b>Текущий план на день:</b> {daily_plan} задач.\n"
        f"{motivation_text}"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "📝 <b>Введите новые задачи на сегодня:</b>\n"
        "• В формате: <code>Клиент1, Курс1, Сумма1, Статус оплаты1</code>\n"
        "• Или опишите текстом (например, 'Добавить ООО Верба на курс Чёрный за 10000 с оплатой'),\n"
        "• Или напишите <code>'нет'</code>, если новых задач нет."
    )
    await update.message.reply_text(welcome_message, parse_mode="HTML")
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
        await update.message.reply_text(
            f"✅ <b>Новых задач не добавлено.</b>\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📅 <b>План на день остаётся:</b> {context.user_data['daily_plan']} задач.",
            parse_mode="HTML"
        )
        return ConversationHandler.END

    # Проверяем, соответствует ли ввод строгому формату
    lines = message_text.split("\n")
    is_strict_format = True
    for line in lines:
        parts = [part.strip() for part in line.split(",")]
        if len(parts) != 4:  # Ожидаем клиент, курс, сумма, статус оплаты
            is_strict_format = False
            break

    if is_strict_format:
        # Обрабатываем строгий формат
        for line in lines:
            parts = [part.strip() for part in line.split(",")]
            client, course, amount, payment_status = parts
            row_data = [client, course, amount, payment_status, "Нет", "bot"]  # Указываем "bot" для "Автор изменений"
            sheet_manager.add_row(row_data)
            new_tasks.append(row_data)
    else:
        prompt = (
            """Ты помощник, преобразующий текст в JSON.
            Твоя задача — анализировать инструкцию и сделать с ней следующее:

            В запросе могут приходить различные названия колонок таблицы. То есть каждый человек может называть их по-разному.
            Вот примерные варианты того, как могут быть названы колонки в запросе на добавление новой записи:
            **Клиент** - [ОАО, ЗАО, ПАО, организация, физическое лицо, юридическое лицо, компания], а также все грамматические формы этих слов в русском языке
            **Курс** - [наш продукт, продукт], а также все грамматические формы этих слов в русском языке
            **Сумма** - [стоимость, стоимость курсов, цена, ценник, цена курса, цена курсов, прайс]. Также если в запросе пришли фразы по типу [курсы стоят, по цене, стоимостью], а дальше стоят цифры, то следует расценивать это как данные для графы "сумма"
            **Статус оплаты** - [подтверждение оплаты]. Если в запросе пришли фразы по типу [клиент оплатил, оплата подтверждена], то есть фразы, которые имеют значение подтверждения оплаты, то статус оплаты будет равен "Да"
            **Подтверждён ли заказ?** - При добавлении это поле всегда заполняется значением "Нет", если не написано в запросе иначе.

            Преобразуй следующую инструкцию в JSON для работы с таблицей.

            Верни результат в виде JSON **массива**, даже если задача одна. Каждый элемент массива — это объект с полями "клиент", "курс", "сумма", "статус оплаты", "Подтверждён ли заказ?".

            Пример твоего ответа:
            [
                {"клиент": "ООО Ромашка", "курс": "Фасад", "сумма": "10000", "статус оплаты": "Да", "Подтверждён ли заказ?": "Нет"},
                {"клиент": "ЗАО Клен", "курс": "Дизайн", "сумма": "15000", "статус оплаты": "Нет", "Подтверждён ли заказ?": "Нет"}
            ]

            Ответь **ТОЛЬКО** в формате JSON массива.\n\n"""
            f"Инструкция: {message_text}\n"
        )

        response = await openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты помощник, преобразующий текст в JSON-команды."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.0
        )
        try:
            # Парсим ответ LLM
            tasks_json_raw = response.choices[0].message.content.strip()
            tasks_json = json.loads(tasks_json_raw)

            # Проверяем, что tasks_json — это список
            if not isinstance(tasks_json, list):
                tasks_json = [tasks_json]  # Преобразуем одиночный объект в список

            for task in tasks_json:
                row_data = [
                    task.get("клиент", ""),
                    task.get("курс", ""),
                    task.get("сумма", ""),
                    task.get("статус оплаты", ""),
                    task.get("Подтверждён ли заказ?", "Нет"),
                    "bot"  # Указываем "bot" для "Автор изменений"
                ]
                # Логируем добавляемую строку для отладки
                logging.info(f"Добавление строки через LLM для менеджера {manager_id}: {row_data}")
                sheet_manager.add_row(row_data)
                new_tasks.append(row_data)
        except (json.JSONDecodeError, AttributeError) as e:
            await update.message.reply_text(
                "❌ <b>Ошибка:</b> не удалось распознать задачи из текста. Попробуйте ещё раз в правильном формате.",
                parse_mode="HTML"
            )
            logging.error(f"Ошибка парсинга LLM ответа: {str(e)}")
            return ADD_TASKS

    # Обновляем план на день
    new_tasks_count = len(new_tasks)
    context.user_data["daily_plan"] += new_tasks_count

    # Формируем подтверждение
    confirmation = (
        "✅ <b>Задачи успешно добавлены!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📋 <b>Добавлено {new_tasks_count} новых задач:</b>\n"
    )
    for task in new_tasks:
        confirmation += f"• {task[0]} | {task[1]} | {task[2]} | Оплата: {task[3]}\n"
    confirmation += f"📅 <b>Обновлённый план на день:</b> {context.user_data['daily_plan']} задач."

    await update.message.reply_text(confirmation, parse_mode="HTML")
    return ConversationHandler.END


async def finish_work_day(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    role = role_manager.get_role(user_id)
    if not role:
        await update.message.reply_text(
            "🚫 <b>Вы не зарегистрированы.</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Обратитесь к директору для регистрации.",
            parse_mode="HTML"
        )
        return ConversationHandler.END

    if not role_manager.is_active(user_id):
        await update.message.reply_text(
            "⚠️ <b>Бот уже отключён для вас.</b>",
            parse_mode="HTML"
        )
        return ConversationHandler.END

    # Принудительно завершаем любой предыдущий диалог
    if context.user_data.get("conversation_state"):
        context.user_data["conversation_state"] = None

    if role_manager.is_manager(user_id):
        manager_id = user_id
        spreadsheet_name = str(manager_id)

        sheet_manager = GoogleSheetManager(spreadsheet_name)
        all_rows = sheet_manager.sheet.get_all_values()[1:]
        deleted_count = 0
        for i, row in enumerate(all_rows[::-1]):
            if len(row) >= 5 and row[4].lower() == "да":  # Проверяем "Подтверждён ли заказ?"
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
            "✅ <b>Подтверждённые заказы удалены из таблицы!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📝 <b>Пожалуйста, напишите краткий фидбек по рабочему дню:</b>\n"
            "• Что получилось,\n"
            "• Что не получилось.",
            parse_mode="HTML"
        )
        return FEEDBACK

    role_manager.set_active(user_id, False)
    await update.message.reply_text(
        "✅ <b>Бот отключён!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🌙 До завтра!",
        parse_mode="HTML"
    )
    return ConversationHandler.END


async def process_feedback(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    feedback = update.message.text

    manager_id = context.user_data["manager_id"]
    closed_count = context.user_data["closed_count"]
    today_stats = context.user_data["today_stats"]
    unclosed_count = context.user_data["unclosed_count"]
    deleted_count = context.user_data["deleted_count"]

    summary = (
        "📊 <b>Сводка по менеджеру {}</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "✅ <b>Закрыто сделок:</b> {}\n"
    ).format(manager_id, closed_count)
    if closed_count > 0:
        summary += "📋 <b>Подробности закрытых сделок:</b>\n"
        for stat in today_stats:
            client_name, course, contract_amount, timestamp = stat
            summary += f"• {client_name} | {course} | {contract_amount} | {timestamp}\n"
    summary += f"⚠️ <b>Незакрытых сделок:</b> {unclosed_count}\n"
    summary += f"🗑️ <b>Удалено подтверждённых записей из таблицы:</b> {deleted_count}\n"
    summary += f"📝 <b>Фидбек менеджера:</b>\n{feedback}"

    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT telegram_id FROM users WHERE role = 'director' LIMIT 1")
        director_id = cursor.fetchone()
        if director_id:
            director_id = director_id[0]
            await context.bot.send_message(chat_id=director_id, text=summary, parse_mode="HTML")
        else:
            logging.warning("Директор не найден в базе данных.")

    role_manager.set_active(user_id, False)
    await update.message.reply_text(
        "✅ <b>Бот отключён!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🌟 <b>Спасибо за фидбек!</b> До завтра!",
        parse_mode="HTML"
    )
    return ConversationHandler.END


async def cancel_feedback(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    role_manager.set_active(user_id, False)
    await update.message.reply_text("❌ Запрос фидбека отменён. Бот отключён.")
    return ConversationHandler.END