from telegram.ext import CallbackContext

from bot.utils.role_manager import role_manager


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
            parse_mode="HTML",
        )


__all__ = ["end_of_day_reminder"]
