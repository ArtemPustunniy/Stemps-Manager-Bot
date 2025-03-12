from typing import Dict
from google_sheets.manager import GoogleSheetManager


class TableCommands:
    ADD_ROW = "add_row"
    UPDATE_CELL = "update_cell"
    DELETE_ROW = "delete_row"


async def execute_command(command: Dict) -> str:
    sheet_manager = GoogleSheetManager("StempsManagement")

    try:
        cmd = command.get("command")
        params = command.get("parameters", {})

        if cmd == TableCommands.ADD_ROW:
            row_data = [
                params.get("клиент", ""),
                params.get("курс", ""),
                params.get("сумма", ""),
                params.get("статус оплаты", ""),
                params.get("Подтверждён ли заказ?", "")
            ]
            sheet_manager.add_row(row_data)
            return f"✅ Добавлена строка: {row_data}"

        elif cmd == TableCommands.UPDATE_CELL:
            client = params.get("клиент", "")
            column = params.get("столбец", "")
            value = params.get("значение", "")  # Новое значение из параметров

            # Ищем строку по клиенту
            row_index = sheet_manager.find_row(client)
            if not row_index:
                return f"❌ Клиент {client} не найден"

            # Определяем индекс столбца
            column_index = {"курс": 2, "сумма": 3, "статус оплаты": 4, "Подтверждён ли заказ?": 5}.get(column)
            if not column_index:
                return f"❌ Неизвестный столбец: {column}"

            sheet_manager.update_cell(row_index, column_index, value)
            return f"✅ Обновлена ячейка ({row_index}, {column}) для клиента {client}: {value}"

        elif cmd == TableCommands.DELETE_ROW:
            client = params.get("клиент", "")
            course = params.get("курс", "")

            # Ищем строку по клиенту и курсу
            row_index = sheet_manager.find_row(client, course)
            if not row_index:
                return f"❌ Клиент {client} с курсом {course} не найден"

            sheet_manager.delete_row(row_index)
            return f"✅ Удалена строка {row_index} для клиента {client}, курс {course}"

        else:
            return f"❌ Неизвестная команда: {cmd}"

    except Exception as e:
        return f"❌ Ошибка выполнения команды: {str(e)}"