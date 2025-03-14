from telegram import Update
from telegram.ext import CallbackContext, CommandHandler
from bot.utils.role_manager import role_manager
from bot.utils.stats_manager import stats_manager
from bot.config.settings import ROLES


async def manage_users(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if not role_manager.is_active(user_id):
        await update.message.reply_text("Бот отключён для вас. Включите его командой /start_work_day.")
        return

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


async def stats(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if not role_manager.is_active(user_id):
        await update.message.reply_text("Бот отключён для вас. Включите его командой /start_work_day.")
        return

    if not role_manager.is_director(user_id):
        await update.message.reply_text("Эта команда доступна только директору.")
        return

    try:
        args = context.args
        if len(args) != 1:
            await update.message.reply_text("Использование: /stats <telegram_id>")
            return

        manager_id = int(args[0])
        if not role_manager.is_manager(manager_id):
            await update.message.reply_text(f"Пользователь {manager_id} не является менеджером.")
            return

        orders = stats_manager.get_manager_stats(manager_id)
        if not orders:
            await update.message.reply_text(f"Менеджер {manager_id} пока не закрыл ни одного заказа.")
            return

        response = f"Статистика менеджера {manager_id}:\n"
        for order in orders:
            client_name, course, contract_amount, timestamp = order
            response += f"- {client_name} | {course} | {contract_amount} | {timestamp}\n"
        await update.message.reply_text(response)
    except ValueError:
        await update.message.reply_text("Telegram ID должен быть числом.")


async def today_revenue(update: Update, context: CallbackContext) -> None:
    """
    Выводит суммарную выручку каждого менеджера за сегодня (подтверждённые заказы).
    Доступно только директору.
    """
    user_id = update.effective_user.id
    if not role_manager.is_active(user_id):
        await update.message.reply_text("Бот отключён для вас. Включите его командой /start_work_day.")
        return

    if not role_manager.is_director(user_id):
        await update.message.reply_text("Эта команда доступна только директору.")
        return

    # Получаем выручку за сегодня для всех менеджеров
    revenue_data = stats_manager.get_today_revenue_by_managers()

    if not revenue_data:
        await update.message.reply_text("Сегодня ни один менеджер не закрыл заказов.")
        return

    response = "Выручка менеджеров за сегодня:\n"
    total_revenue = 0.0
    for manager_id, revenue in revenue_data.items():
        response += f"- Менеджер {manager_id}: {revenue:.2f}\n"
        total_revenue += revenue

    response += f"\nОбщая выручка за сегодня: {total_revenue:.2f}"
    await update.message.reply_text(response)


def setup_handlers(application):
    application.add_handler(CommandHandler("manage_users", manage_users))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("today_revenue", today_revenue))