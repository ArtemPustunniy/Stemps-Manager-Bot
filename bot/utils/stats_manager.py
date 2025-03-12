import sqlite3
from datetime import datetime


class StatsManager:
    def __init__(self, db_path: str = "users.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Инициализация таблицы closed_orders."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS closed_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    manager_id INTEGER NOT NULL,
                    client_name TEXT NOT NULL,
                    course TEXT NOT NULL,
                    contract_amount TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            """)
            conn.commit()

    def add_closed_order(self, manager_id: int, client_name: str, course: str, contract_amount: str):
        """Добавление записи о закрытом заказе."""
        timestamp = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO closed_orders (manager_id, client_name, course, contract_amount, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """, (manager_id, client_name, course, contract_amount, timestamp))
            conn.commit()

    def get_manager_stats(self, manager_id: int) -> list:
        """Получение статистики по менеджеру."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT client_name, course, contract_amount, timestamp
                FROM closed_orders
                WHERE manager_id = ?
                ORDER BY timestamp DESC
            """, (manager_id,))
            return cursor.fetchall()


# Глобальный экземпляр
stats_manager = StatsManager()