from typing import Dict
from google_sheets.manager import GoogleSheetManager
from bot.utils.stats_manager import stats_manager
import sqlite3
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class TableCommands:
    ADD_ROW = "add_row"
    UPDATE_CELL = "update_cell"
    DELETE_ROW = "delete_row"


async def execute_command(
    command: Dict, spreadsheet_name: str, manager_id: int, bot=None, context=None
) -> str:
    sheet_manager = GoogleSheetManager(spreadsheet_name)

    try:
        cmd = command.get("command")
        params = command.get("parameters", {})
        logging.info(f"Получена команда: {command}")

        notification = None

        if cmd == TableCommands.ADD_ROW:
            row_data = [
                params.get("клиент", ""),
                params.get("курс", ""),
                params.get("сумма", ""),
                params.get("статус оплаты", ""),
                params.get("Подтверждён ли заказ?", ""),
                "bot",
            ]
            logging.info(f"Добавление строки: {row_data}")
            sheet_manager.add_row(row_data)
            if params.get("Подтверждён ли заказ?", "").lower() == "да":
                stats_manager.add_closed_order(
                    manager_id=manager_id,
                    client_name=row_data[0],
                    course=row_data[1],
                    contract_amount=row_data[2],
                )
                result = (
                    "✅ <b>Добавлена строка:</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"{row_data[0]} | {row_data[1]} | {row_data[2]} | {row_data[3]}\n"
                    "✅ <b>Заказ подтверждён и добавлен в статистику!</b>"
                )
            else:
                result = (
                    "✅ <b>Добавлена строка:</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"{row_data[0]} | {row_data[1]} | {row_data[2]} | {row_data[3]}"
                )
            notification = (
                "📝 <b>Уведомление:</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Менеджер <b>{manager_id}</b> добавил строку в таблицу <b>{spreadsheet_name}</b>:\n"
                f"{row_data[0]} | {row_data[1]} | {row_data[2]} | {row_data[3]}"
            )

        elif cmd == TableCommands.UPDATE_CELL:
            client = params.get("клиент", "")
            column = params.get("столбец", "")
            value = params.get("значение", "")

            row_index = sheet_manager.find_row(client)
            if not row_index:
                return (
                    "❌ <b>Ошибка:</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"Клиент <b>{client}</b> не найден."
                )

            column_index = {
                "курс": 2,
                "сумма": 3,
                "статус оплаты": 4,
                "Подтверждён ли заказ?": 5,
            }.get(column)
            if not column_index:
                return (
                    "❌ <b>Ошибка:</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"Неизвестный столбец: <b>{column}</b>"
                )

            old_value = sheet_manager.read_cell(row_index, column_index)
            sheet_manager.update_cell(row_index, column_index, value)

            if (
                column == "Подтверждён ли заказ?"
                and value.lower() == "да"
                and old_value.lower() != "да"
            ):
                row_data = sheet_manager.sheet.row_values(row_index)
                stats_manager.add_closed_order(
                    manager_id=manager_id,
                    client_name=row_data[0],
                    course=row_data[1],
                    contract_amount=row_data[2],
                )
                result = (
                    "✅ <b>Ячейка обновлена:</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"Клиент: <b>{client}</b> (строка {row_index}, столбец '{column}'):\n"
                    f"Новое значение: <b>{value}</b>\n"
                    "✅ <b>Заказ подтверждён и добавлен в статистику!</b>"
                )

                if context and bot:
                    context.user_data["completed_today"] = (
                        context.user_data.get("completed_today", 0) + 1
                    )
                    daily_plan = context.user_data.get("daily_plan", 10)
                    progress = context.user_data["completed_today"] / daily_plan
                    last_milestone = context.user_data.get("last_milestone", 0)
                    current_milestone = int(progress * 5) / 5

                    if current_milestone > last_milestone and current_milestone <= 1.0:
                        motivation_messages = [
                            "🎉 Отлично, 20% плана в кармане! Ты на верном пути!",
                            "🚀 Уже 40% — ты как ракета, набираешь высоту!",
                            "💪 60% позади, ты неудержим! Продолжай в том же духе!",
                            "🏁 80% плана выполнено — финишная прямая, ты почти чемпион!",
                            "🏆 100% — план выполнен! Ты настоящий герой дня!",
                        ]
                        milestone_index = int(current_milestone * 5) - 1
                        motivation_text = motivation_messages[milestone_index]
                        await bot.send_message(
                            chat_id=manager_id, text=motivation_text, parse_mode="HTML"
                        )
                        context.user_data["last_milestone"] = current_milestone

            else:
                result = (
                    "✅ <b>Ячейка обновлена:</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"Клиент: <b>{client}</b> (строка {row_index}, столбец '{column}'):\n"
                    f"Новое значение: <b>{value}</b>"
                )
            notification = (
                "📝 <b>Уведомление:</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Менеджер <b>{manager_id}</b> обновил ячейку в таблице <b>{spreadsheet_name}</b>:\n"
                f"Клиент: <b>{client}</b>, столбец '{column}' с '{old_value}' на '{value}'"
            )

        elif cmd == TableCommands.DELETE_ROW:
            client = params.get("клиент", "")
            course = params.get("курс", "")

            row_index = sheet_manager.find_row(client, course)
            if not row_index:
                return (
                    "❌ <b>Ошибка:</b>\n"
                    "━━━━━━━━━━━━━━━━━━━━━━━\n"
                    f"Клиент <b>{client}</b> с курсом <b>{course}</b> не найден."
                )

            sheet_manager.delete_row(row_index)
            result = (
                "✅ <b>Строка удалена:</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Строка <b>{row_index}</b> (Клиент: <b>{client}</b>, Курс: <b>{course}</b>)"
            )
            notification = (
                "🗑️ <b>Уведомление:</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Менеджер <b>{manager_id}</b> удалил строку из таблицы <b>{spreadsheet_name}</b>:\n"
                f"Клиент: <b>{client}</b>, Курс: <b>{course}</b>"
            )

        else:
            return (
                "❌ <b>Ошибка:</b>\n"
                "━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"Неизвестная команда: <b>{cmd}</b>"
            )

        if bot and notification:
            try:
                with sqlite3.connect("users.db") as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT telegram_id FROM users WHERE role = 'director'")
                    directors = cursor.fetchall()
                    for director in directors:
                        director_id = director[0]
                        await bot.send_message(
                            chat_id=director_id, text=notification, parse_mode="HTML"
                        )
            except Exception as e:
                logging.error(
                    f"Ошибка при отправке уведомления директору: {str(e)}",
                    exc_info=True,
                )

        return result

    except Exception as e:
        logging.error(f"Ошибка выполнения команды: {str(e)}", exc_info=True)
        return (
            "❌ <b>Ошибка выполнения команды:</b>\n"
            "━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"{str(e)}"
        )
