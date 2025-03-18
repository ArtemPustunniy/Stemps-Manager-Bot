from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler

from bot.utils.role_manager import role_manager
from bot.utils.stats_manager import stats_manager
from google_sheets.manager import GoogleSheetManager
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

FEEDBACK = 1


async def finish_work_day(update: Update, context: CallbackContext) -> int:
    user_id = update.effective_user.id
    role = role_manager.get_role(user_id)
    if not role:
        await update.message.reply_text(
            "🚫 <b>Вы не зарегистрированы.</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            "Обратитесь к директору для регистрации.",
            parse_mode="HTML",
        )
        return ConversationHandler.END

    if not role_manager.is_active(user_id):
        await update.message.reply_text(
            "⚠️ <b>Бот уже отключён для вас.</b>", parse_mode="HTML"
        )
        return ConversationHandler.END

    if context.user_data.get("conversation_state"):
        context.user_data["conversation_state"] = None

    if role_manager.is_manager(user_id):
        manager_id = user_id
        spreadsheet_name = str(manager_id)

        sheet_manager = GoogleSheetManager(spreadsheet_name)
        all_rows = sheet_manager.sheet.get_all_values()[1:]
        deleted_count = 0
        for i, row in enumerate(all_rows[::-1]):
            if (
                len(row) >= 5 and row[4].lower() == "да"
            ):  # Проверяем "Подтверждён ли заказ?"
                row_index = len(all_rows) - i + 1
                sheet_manager.delete_row(row_index)
                deleted_count += 1

        today_stats = stats_manager.get_today_stats(manager_id)
        closed_count = len(today_stats)

        all_rows = sheet_manager.sheet.get_all_values()[1:]
        unclosed_count = sum(
            1 for row in all_rows if len(row) >= 5 and row[4].lower() == "нет"
        )

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
            parse_mode="HTML",
        )
        return FEEDBACK

    role_manager.set_active(user_id, False)
    await update.message.reply_text(
        "✅ <b>Бот отключён!</b>\n" "━━━━━━━━━━━━━━━━━━━━━━━\n" "🌙 До завтра!",
        parse_mode="HTML",
    )
    return ConversationHandler.END


__all__ = ["finish_work_day"]
