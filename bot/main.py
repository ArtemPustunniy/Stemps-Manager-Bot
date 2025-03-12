import sqlite3

from telegram.ext import Application, CommandHandler, MessageHandler, filters, ConversationHandler
from bot.config.settings import TOKEN, CLIENT_NAME, COURSE, CONTRACT_AMOUNT, PAYMENT_STATUS, PLAN, LLM_ADD
from bot.handlers.basic_handlers import start, help_command, myid  # Добавляем myid
from bot.handlers.add_handlers import add, get_client_name, get_course, get_contract_amount, get_payment_status, get_plan, cancel
from bot.handlers.llm_handlers import llm_add, process_llm_instruction
from bot.handlers.admin_handlers import setup_handlers as setup_admin_handlers
from bot.utils.role_manager import role_manager


def main():
    app = Application.builder().token(TOKEN).build()

    # Проверка и регистрация первого директора
    def check_first_director(update, context):
        # user_id = update.effective_user.id
        # if role_manager.get_role(user_id) is None:  # Если пользователь не зарегистрирован
        #     with sqlite3.connect("users.db") as conn:
        #         cursor = conn.cursor()
        #         cursor.execute("SELECT COUNT(*) FROM users")
        #         user_count = cursor.fetchone()[0]
        #         if user_count == 0:  # Если база пуста
        #             role_manager.add_user(user_id, "director")
        #             update.message.reply_text(
        #                 f"Вы первый пользователь и автоматически назначены директором!\n"
        #                 f"Ваш Telegram ID: {user_id}"
        #             )
        return start(update, context)

    app.add_handler(CommandHandler("start", check_first_director))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("myid", myid))  # Добавляем обработчик для /myid

    setup_admin_handlers(app)

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("add", add),
            CommandHandler("AI_assistent", llm_add)
        ],
        states={
            CLIENT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_client_name)],
            COURSE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_course)],
            CONTRACT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_contract_amount)],
            PAYMENT_STATUS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_payment_status)],
            PLAN: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_plan)],
            LLM_ADD: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_llm_instruction)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv_handler)
    print("🤖 Бот запущен!")
    app.run_polling()


if __name__ == "__main__":
    main()
