import logging
from bot.config.settings import OPENAI_API_KEY
from openai import AsyncOpenAI

from bot.handlers.basic_handlers_folder.start_handler import start
from bot.handlers.basic_handlers_folder.help_command_handler import help_command
from bot.handlers.basic_handlers_folder.myid_handler import myid
from bot.handlers.basic_handlers_folder.end_of_day_reminder_handler import (
    end_of_day_reminder,
)
from bot.handlers.basic_handlers_folder.start_work_day_handler import start_work_day
from bot.handlers.basic_handlers_folder.process_new_tasks_handler import (
    process_new_tasks,
)
from bot.handlers.basic_handlers_folder.finish_work_day_handler import finish_work_day
from bot.handlers.basic_handlers_folder.process_feedback_handler import process_feedback
from bot.handlers.basic_handlers_folder.cancel_feedback_handler import cancel_feedback

openai_client = AsyncOpenAI(api_key=OPENAI_API_KEY)

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


__all__ = [
    "start",
    "help_command",
    "myid",
    "end_of_day_reminder",
    "start_work_day",
    "process_new_tasks",
    "finish_work_day",
    "process_feedback",
    "cancel_feedback",
]
