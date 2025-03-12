import os
from dotenv import load_dotenv
import logging

load_dotenv()

TOKEN = os.getenv("TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Состояния для пошагового добавления
CLIENT_NAME, COURSE, CONTRACT_AMOUNT, PAYMENT_STATUS, PLAN, LLM_ADD = range(6)

# Роли пользователей
ROLES = {
    "DIRECTOR": "director",
    "MANAGER": "manager"
}

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
