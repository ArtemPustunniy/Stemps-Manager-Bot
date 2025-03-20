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
