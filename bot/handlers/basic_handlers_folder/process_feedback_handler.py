from telegram import Update
from telegram.ext import CallbackContext, ConversationHandler
from bot.utils.role_manager import role_manager
import sqlite3
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


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
        cursor.execute("SELECT telegram_id FROM users WHERE role = 'director'")
        directors = cursor.fetchall()
        if directors:
            for director in directors:
                director_id = director[0]
                try:
                    await context.bot.send_message(
                        chat_id=director_id, text=summary, parse_mode="HTML"
                    )
                except Exception as e:
                    logging.error(f"Ошибка отправки сообщения директору {director_id}: {e}")
        else:
            logging.warning("Директора не найдены в базе данных.")

    role_manager.set_active(user_id, False)
    await update.message.reply_text(
        "✅ <b>Бот отключён!</b>\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🌟 <b>Спасибо за фидбек!</b> До завтра!",
        parse_mode="HTML",
    )
    return ConversationHandler.END


__all__ = ["process_feedback"]
