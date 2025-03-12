from google_sheets.manager import GoogleSheetManager
from .telegram import send_telegram_message

sheet_manager = GoogleSheetManager("StempsManagement")

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