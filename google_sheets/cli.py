from .manager import GoogleSheetManager


def main():
    sheet_manager = GoogleSheetManager("StempsManagement")

    while True:
        print("\nВыберите действие:")
        print("1. Показать все данные")
        print("2. Прочитать ячейку")
        print("3. Добавить новую запись")
        print("4. Обновить ячейку")
        print("5. Удалить запись")
        print("6. Найти строку по клиенту и курсу")
        print("7. Выход")

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
            plan = input("ППодтверждён ли заказ? ")

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
            client = input("Введите название клиента: ")
            course = input("Введите курс (или оставьте пустым): ")
            course = course if course.strip() else None
            row_index = sheet_manager.find_row(client, course)
            if row_index:
                print(f"Строка найдена: {row_index}")
            else:
                print("Строка не найдена")

        elif choice == "7":
            print("Выход...")
            break

        else:
            print("Неверный ввод, попробуйте снова.")

if __name__ == "__main__":
    main()