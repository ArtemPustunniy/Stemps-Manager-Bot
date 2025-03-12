import pandas as pd
from .client import connect_to_google_sheets


class GoogleSheetManager:
    def __init__(self, spreadsheet_name: str):
        self.client = connect_to_google_sheets()
        try:
            self.sheet = self.client.open(spreadsheet_name).sheet1
        except Exception:
            # Если таблицы нет, создаём новую
            self.sheet = self.client.create(spreadsheet_name).sheet1
            # Задаём заголовки
            headers = ["Название клиента", "Название курса", "Сумма договора", "Статус оплаты", "Подтверждён ли заказ?"]
            self.sheet.append_row(headers)

    def read_all_data(self):
        data = self.sheet.get_all_records()
        return pd.DataFrame(data)

    def read_cell(self, row, col):
        return self.sheet.cell(row, col).value

    def add_row(self, row_data):
        self.sheet.append_row(row_data)
        return "Row added successfully"

    def update_cell(self, row, col, value):
        self.sheet.update_cell(row, col, value)
        return f"Cell ({row}, {col}) updated"

    def delete_row(self, row_number):
        self.sheet.delete_rows(row_number)
        return f"Row {row_number} deleted"

    def find_row(self, client: str, course: str = None) -> int | None:
        data = self.sheet.get_all_values()
        if not data:
            return None

        for row_index, row in enumerate(data[1:], start=2):  # Начинаем с 2, пропуская заголовки
            row_client = row[0] if len(row) > 0 else ""
            row_course = row[1] if len(row) > 1 else ""

            if course is None:
                if row_client == client:
                    return row_index
            else:
                if row_client == client and row_course == course:
                    return row_index
        return None