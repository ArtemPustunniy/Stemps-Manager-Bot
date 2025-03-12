from typing import Dict
from google_sheets.manager import GoogleSheetManager
from bot.utils.stats_manager import stats_manager


class TableCommands:
    ADD_ROW = "add_row"
    UPDATE_CELL = "update_cell"
    DELETE_ROW = "delete_row"


async def execute_command(command: Dict, spreadsheet_name: str, manager_id: int) -> str:
    sheet_manager = GoogleSheetManager(spreadsheet_name)

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
            # Если заказ подтверждён при добавлении
            if params.get("Подтверждён ли заказ?", "").lower() == "да":
                stats_manager.add_closed_order(
                    manager_id=manager_id,
                    client_name=row_data[0],
                    course=row_data[1],
                    contract_amount=row_data[2]
                )
                return f"✅ Добавлена строка: {row_data}\n✅ Заказ подтверждён и добавлен в статистику!"
            return f"✅ Добавлена строка: {row_data}"

        elif cmd == TableCommands.UPDATE_CELL:
            client = params.get("клиент", "")
            column = params.get("столбец", "")
            value = params.get("значение", "")

            row_index = sheet_manager.find_row(client)
            if not row_index:
                return f"❌ Клиент {client} не найден"

            column_index = {"курс": 2, "сумма": 3, "статус оплаты": 4, "Подтверждён ли заказ?": 5}.get(column)
            if not column_index:
                return f"❌ Неизвестный столбец: {column}"

            # Проверяем, было ли значение "Да" раньше
            old_value = sheet_manager.read_cell(row_index, column_index)
            sheet_manager.update_cell(row_index, column_index, value)

            # Если обновляем "Подтверждён ли заказ?" на "Да" и ранее оно не было "Да"
            if column == "Подтверждён ли заказ?" and value.lower() == "да" and old_value.lower() != "да":
                row_data = sheet_manager.sheet.row_values(row_index)
                stats_manager.add_closed_order(
                    manager_id=manager_id,
                    client_name=row_data[0],
                    course=row_data[1],
                    contract_amount=row_data[2]
                )
                return f"✅ Обновлена ячейка ({row_index}, {column}) для клиента {client}: {value}\n✅ Заказ подтверждён и добавлен в статистику!"
            return f"✅ Обновлена ячейка ({row_index}, {column}) для клиента {client}: {value}"

        elif cmd == TableCommands.DELETE_ROW:
            client = params.get("клиент", "")
            course = params.get("курс", "")

            row_index = sheet_manager.find_row(client, course)
            if not row_index:
                return f"❌ Клиент {client} с курсом {course} не найден"

            sheet_manager.delete_row(row_index)
            return f"✅ Удалена строка {row_index} для клиента {client}, курс {course}"

        else:
            return f"❌ Неизвестная команда: {cmd}"

    except Exception as e:
        return f"❌ Ошибка выполнения команды: {str(e)}"