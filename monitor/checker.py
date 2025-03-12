import sqlite3

import pandas as pd
from google_sheets.manager import GoogleSheetManager
from .telegram import send_telegram_message
from bot.utils.role_manager import role_manager


async def check_for_updates(redis_client):
    """
    Проверяет обновления во всех таблицах менеджеров и отправляет уведомления.
    """
    # Получаем список всех менеджеров
    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT telegram_id FROM users WHERE role = 'manager'")
        manager_ids = [row[0] for row in cursor.fetchall()]

    for manager_id in manager_ids:
        spreadsheet_name = str(manager_id)
        sheet_manager = GoogleSheetManager(spreadsheet_name)
        data = sheet_manager.read_all_data()
        data_str = str(data.to_dict())

        redis_key = f"google_sheets_data_{manager_id}"
        old_data_str = await redis_client.get(redis_key, encoding="utf-8")

        if old_data_str is None:
            await redis_client.set(redis_key, data_str)
            continue

        if data_str != old_data_str:
            await send_telegram_message(f"🔔 В таблице менеджера {manager_id} произошли изменения!")
            await redis_client.set(redis_key, data_str)