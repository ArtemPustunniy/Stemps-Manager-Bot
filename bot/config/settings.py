import os
from dotenv import load_dotenv
import logging

load_dotenv()

TOKEN = os.getenv("TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

CLIENT_NAME, COURSE, CONTRACT_AMOUNT, PAYMENT_STATUS, PLAN, LLM_ADD = range(6)

ROLES = {"DIRECTOR": "director", "MANAGER": "manager"}

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
