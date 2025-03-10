import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd


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


def main():
    sheet_manager = GoogleSheetManager("StempsManagement")

    while True:
        print("\nВыберите действие:")
        print("1. Показать все данные")
        print("2. Прочитать ячейку")
        print("3. Добавить новую запись")
        print("4. Обновить ячейку")
        print("5. Удалить запись")
        print("6. Выход")

        choice = input("\nВведите номер действия: ")

        if choice == "1":
            print("\nВсе данные из таблицы:")
            print(sheet_manager.read_all_data())

        elif choice == "2":
            row = int(input("Введите номер строки: "))
            col = int(input("Введите номер столбца: "))
            print(f"\nЗначение в ({row}, {col}): {sheet_manager.read_cell(row, col)}")

        elif choice == "3":
            client_name = input("Название клиента: ")
            course = input("Курс(ы): ")
            contract_amount = input("Сумма договора: ")
            payment_status = input("Оплата произведена (Да/Нет): ")
            plan = input("План недели/месяца: ")

            new_row = [client_name, course, contract_amount, payment_status, plan]
            print(sheet_manager.add_row(new_row))

        elif choice == "4":
            row = int(input("Введите номер строки: "))
            col = int(input("Введите номер столбца: "))
            value = input("Введите новое значение: ")
            print(sheet_manager.update_cell(row, col, value))

        elif choice == "5":
            row_number = int(input("Введите номер строки для удаления: "))
            print(sheet_manager.delete_row(row_number))

        elif choice == "6":
            print("Выход...")
            break

        else:
            print("Неверный ввод, попробуйте снова.")


if __name__ == "__main__":
    main()
