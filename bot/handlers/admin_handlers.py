from telegram import Update
from telegram.ext import CallbackContext, CommandHandler
from bot.utils.role_manager import role_manager
from bot.utils.stats_manager import stats_manager
from bot.config.settings import ROLES


async def manage_users(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if not role_manager.is_active(user_id):
        await update.message.reply_text(
            "⚠️ <b>Бот отключён для вас.</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Включите его командой <code>/start_work_day</code>.",
            parse_mode="HTML",
        )
        return

    if not role_manager.is_director(user_id):
        await update.message.reply_text(
            "🚫 <b>Доступ запрещён.</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Эта команда доступна только директору.",
            parse_mode="HTML",
        )
        return

    try:
        args = context.args
        if len(args) != 2:
            await update.message.reply_text(
                "❌ <b>Неверный формат команды.</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                "<b>Использование:</b> <code>/manage_users &lt;telegram_id&gt; &lt;role&gt;</code>\n"
                "<b>Роли:</b> director, manager",
                parse_mode="HTML",
            )
            return

        target_id = int(args[0])
        role = args[1].lower()
        if role not in [ROLES["DIRECTOR"], ROLES["MANAGER"]]:
            await update.message.reply_text(
                "❌ <b>Неверная роль.</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                "<b>Доступные роли:</b> director, manager",
                parse_mode="HTML",
            )
            return

        role_manager.add_user(target_id, role)
        await update.message.reply_text(
            "✅ <b>Пользователь успешно добавлен!</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"Пользователь <b>{target_id}</b> добавлен с ролью <b>{role}</b>.",
            parse_mode="HTML",
        )
    except ValueError:
        await update.message.reply_text(
            "❌ <b>Ошибка:</b> Telegram ID должен быть числом.", parse_mode="HTML"
        )


async def stats(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if not role_manager.is_active(user_id):
        await update.message.reply_text(
            "⚠️ <b>Бот отключён для вас.</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Включите его командой <code>/start_work_day</code>.",
            parse_mode="HTML",
        )
        return

    if not role_manager.is_director(user_id):
        await update.message.reply_text(
            "🚫 <b>Доступ запрещён.</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Эта команда доступна только директору.",
            parse_mode="HTML",
        )
        return

    try:
        args = context.args
        if len(args) != 1:
            await update.message.reply_text(
                "❌ <b>Неверный формат команды.</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                "<b>Использование:</b> <code>/stats <telegram_id></code>",
                parse_mode="HTML",
            )
            return

        manager_id = int(args[0])
        if not role_manager.is_manager(manager_id):
            await update.message.reply_text(
                "⚠️ <b>Ошибка:</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Пользователь <b>{manager_id}</b> не является менеджером.",
                parse_mode="HTML",
            )
            return

        orders = stats_manager.get_manager_stats(manager_id)
        if not orders:
            await update.message.reply_text(
                "ℹ️ <b>Информация:</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Менеджер <b>{manager_id}</b> пока не закрыл ни одного заказа.",
                parse_mode="HTML",
            )
            return

        response = (
            "📊 <b>Статистика менеджера {}</b>\n" "━━━━━━━━━━━━━━━━━━━━━━━\n"
        ).format(manager_id)
        for order in orders:
            client_name, course, contract_amount, timestamp = order
            response += (
                f"• {client_name} | {course} | {contract_amount} | {timestamp}\n"
            )
        await update.message.reply_text(response, parse_mode="HTML")
    except ValueError:
        await update.message.reply_text(
            "❌ <b>Ошибка:</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Telegram ID должен быть числом.",
            parse_mode="HTML",
        )


async def today_revenue(update: Update, context: CallbackContext) -> None:
    """
    Выводит суммарную выручку каждого менеджера за сегодня (подтверждённые заказы).
    Доступно только директору.
    """
    user_id = update.effective_user.id
    if not role_manager.is_active(user_id):
        await update.message.reply_text(
            "⚠️ <b>Бот отключён для вас.</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Включите его командой <code>/start_work_day</code>.",
            parse_mode="HTML",
        )
        return

    if not role_manager.is_director(user_id):
        await update.message.reply_text(
            "🚫 <b>Доступ запрещён.</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Эта команда доступна только директору.",
            parse_mode="HTML",
        )
        return

    revenue_data = stats_manager.get_today_revenue_by_managers()

    if not revenue_data:
        await update.message.reply_text(
            "ℹ️ <b>Информация:</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Сегодня ни один менеджер не закрыл заказов.",
            parse_mode="HTML",
        )
        return

    response = "💰 <b>Выручка менеджеров за сегодня:</b>\n" "━━━━━━━━━━━━━━━━━━━━━━━\n"
    total_revenue = 0.0
    for manager_id, revenue in revenue_data.items():
        response += f"• Менеджер {manager_id}: <b>{revenue:.2f}</b>\n"
        total_revenue += revenue

    response += f"━━━━━━━━━━━━━━━━━━━━━━━\n💵 <b>Общая выручка за сегодня:</b> {total_revenue:.2f}"
    await update.message.reply_text(response, parse_mode="HTML")


def setup_handlers(application):
    application.add_handler(CommandHandler("manage_users", manage_users))
    application.add_handler(CommandHandler("stats", stats))
    application.add_handler(CommandHandler("today_revenue", today_revenue))
