import pandas as pd
from .client import connect_to_google_sheets


class GoogleSheetManager:
    def __init__(self, spreadsheet_name):
        self.client = connect_to_google_sheets()
        self.sheet = self.client.open(spreadsheet_name).sheet1

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

        # Предполагаем, что заголовки: Клиент (col 0), Курс (col 1), Сумма (col 2), Оплачено (col 3), План (col 4)
        for row_index, row in enumerate(data[1:], start=2):  # Начинаем с 2, так как 1-я строка — заголовки
            row_client = row[0] if len(row) > 0 else ""
            row_course = row[1] if len(row) > 1 else ""

            # Если курс не указан, ищем только по клиенту
            if course is None:
                if row_client == client:
                    return row_index
            # Ищем по клиенту и курсу
            else:
                if row_client == client and row_course == course:
                    return row_index
        return None