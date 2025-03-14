import gspread
from oauth2client.service_account import ServiceAccountCredentials


def connect_to_google_sheets():
    scope = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]

    credentials = ServiceAccountCredentials.from_json_keyfile_name(
        "stempsmanagerbot-3b6400c72024.json", scope
    )

    client = gspread.authorize(credentials)
    return client


def setup_sheet(spreadsheet_name):
    client = connect_to_google_sheets()
    sheet = client.open(spreadsheet_name).sheet1

    HEADERS = [
        "Название клиента",
        "Название курса",
        "Сумма договора для оплаты (ждёт подтверждения)",
        "Статус оплаты",
        "Подтверждён ли заказ?",
        "Автор изменений",
    ]

    existing_headers = sheet.row_values(1)
    if existing_headers != HEADERS:
        sheet.update("A1:F1", [HEADERS])
        print("✅ Заголовки установлены.")
    else:
        print("⚠️ Заголовки уже существуют.")


if __name__ == "__main__":
    # setup_sheet("StempsManagement")
    setup_sheet("738203440")
