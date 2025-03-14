import sqlite3
import pandas as pd
import io
from google_sheets.manager import GoogleSheetManager
from .telegram import send_telegram_message
from bot.utils.role_manager import role_manager


async def check_for_updates(redis_client):
    """
    Проверяет обновления во всех таблицах менеджеров, сравнивает старые и новые данные,
    и отправляет уведомления с указанием добавленных строк, обновлённых ячеек и удалённых строк,
    только если изменение не от бота.
    """
    # Получаем список всех менеджеров
    with sqlite3.connect("users.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT telegram_id FROM users WHERE role = 'manager'")
        manager_ids = [row[0] for row in cursor.fetchall()]

    for manager_id in manager_ids:
        spreadsheet_name = str(manager_id)
        sheet_manager = GoogleSheetManager(spreadsheet_name)
        new_data = sheet_manager.read_all_data()

        # Убедимся, что у нас есть колонка "Автор изменений"
        if 'Автор изменений' not in new_data.columns:
            new_data['Автор изменений'] = ''  # Добавляем колонку, если её нет

        # Ключ для хранения данных в Redis
        redis_key = f"google_sheets_data_{manager_id}"
        old_data_str = await redis_client.get(redis_key, encoding="utf-8")

        if old_data_str is None:
            # Если данных в Redis ещё нет, сохраняем новые данные и продолжаем
            await redis_client.set(redis_key, new_data.to_json())
            continue

        # Проверяем, что строка не пустая и содержит валидный JSON
        if not old_data_str or not old_data_str.strip():
            await send_telegram_message(f"Ошибка: пустые данные в Redis для менеджера {manager_id}. Сбрасываю и сохраняю новые данные.")
            await redis_client.set(redis_key, new_data.to_json())
            continue

        try:
            # Читаем старые данные с использованием StringIO
            old_data = pd.read_json(io.StringIO(old_data_str))
            # Убедимся, что у старых данных тоже есть колонка "Автор изменений"
            if 'Автор изменений' not in old_data.columns:
                old_data['Автор изменений'] = ''
        except ValueError as e:
            await send_telegram_message(f"Ошибка парсинга JSON для менеджера {manager_id}: {str(e)}. Сбрасываю и сохраняю новые данные.")
            await redis_client.set(redis_key, new_data.to_json())
            continue

        # Фильтруем данные, чтобы исключить изменения, сделанные ботом
        old_data_bot_changes = old_data[old_data['Автор изменений'] == 'bot'].index
        new_data_bot_changes = new_data[new_data['Автор изменений'] == 'bot'].index

        # Удаляем строки, изменённые ботом, из сравнения
        old_data_filtered = old_data.drop(old_data_bot_changes)
        new_data_filtered = new_data.drop(new_data_bot_changes)

        # Формируем сообщение об изменениях
        message = f"🔔 В таблице менеджера {manager_id} произошли изменения (не от бота):\n"
        changes = []

        # 1. Обновление ячеек
        if not old_data_filtered.empty and not new_data_filtered.empty:
            # Выравниваем индексы для корректного сравнения
            common_indices = old_data_filtered.index.intersection(new_data_filtered.index)
            if not common_indices.empty:
                old_common = old_data_filtered.loc[common_indices].reset_index(drop=True)
                new_common = new_data_filtered.loc[common_indices].reset_index(drop=True)
                # Сравниваем только общие строки
                for idx in range(len(old_common)):
                    for col in old_common.columns:
                        if col == 'Автор изменений':
                            continue
                        old_value = old_common.iloc[idx][col]
                        new_value = new_common.iloc[idx][col]
                        if pd.isna(old_value) and pd.isna(new_value):
                            continue
                        if old_value != new_value:
                            changes.append(
                                f"- Ячейка [{common_indices[idx]}, {col}]: изменилась с '{old_value}' на '{new_value}'"
                            )

        # 2. Добавленные строки
        added_rows = set(new_data_filtered.index) - set(old_data_filtered.index)
        if added_rows:
            for idx in added_rows:
                row_data = new_data_filtered.loc[idx].drop('Автор изменений').to_dict()
                changes.append(f"- Строка {idx} добавлена: {row_data}")

        # 3. Удалённые строки
        deleted_rows = set(old_data_filtered.index) - set(new_data_filtered.index)
        if deleted_rows:
            for idx in deleted_rows:
                changes.append(f"- Строка {idx} удалена")

        if changes:
            message += "\n".join(changes)
        else:
            message += "Изменения обнаружены, но все они от бота."

        # Отправляем уведомление, если есть изменения
        if changes:
            await send_telegram_message(message)

        # Обновляем данные в Redis
        await redis_client.set(redis_key, new_data.to_json())