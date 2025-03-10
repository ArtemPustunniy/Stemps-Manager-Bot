import time
import os
import asyncio
from dotenv import load_dotenv
from telegram import Bot
from google_sheets import GoogleSheetManager
import aioredis

load_dotenv()
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

sheet_manager = GoogleSheetManager("StempsManagement")

bot = Bot(token=TOKEN)


async def get_redis_client():
    return await aioredis.create_redis_pool("redis://localhost")


async def send_telegram_message(message):
    await bot.send_message(chat_id=CHAT_ID, text=message)


async def check_for_updates(redis_client):
    """
    Проверяет обновления в таблице и отправляет уведомления в Telegram.
    """
    data = sheet_manager.read_all_data()

    data_str = str(data.to_dict())

    old_data_str = await redis_client.get("google_sheets_data", encoding="utf-8")

    if old_data_str is None:
        await redis_client.set("google_sheets_data", data_str)
        return

    if data_str != old_data_str:
        await send_telegram_message("🔔 В таблице произошли изменения!")

        await redis_client.set("google_sheets_data", data_str)


async def main():
    print("📡 Запуск мониторинга Google Таблицы...")

    redis_client = await get_redis_client()

    while True:
        await check_for_updates(redis_client)
        await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())
