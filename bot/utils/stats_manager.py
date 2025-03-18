import sqlite3
from datetime import datetime, timedelta


class StatsManager:
    def __init__(self, db_path: str = "users.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Инициализация таблицы closed_orders."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS closed_orders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    manager_id INTEGER NOT NULL,
                    client_name TEXT NOT NULL,
                    course TEXT NOT NULL,
                    contract_amount TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                )
            """
            )
            conn.commit()

    def add_closed_order(
        self, manager_id: int, client_name: str, course: str, contract_amount: str
    ):
        """Добавление записи о закрытом заказе."""
        timestamp = datetime.now().isoformat()
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO closed_orders (manager_id, client_name, course, contract_amount, timestamp)
                VALUES (?, ?, ?, ?, ?)
            """,
                (manager_id, client_name, course, contract_amount, timestamp),
            )
            conn.commit()

    def get_manager_stats(self, manager_id: int) -> list:
        """Получение статистики по менеджеру."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT client_name, course, contract_amount, timestamp
                FROM closed_orders
                WHERE manager_id = ?
                ORDER BY timestamp DESC
            """,
                (manager_id,),
            )
            return cursor.fetchall()

    def get_yesterday_stats(self, manager_id: int) -> list:
        """Получение статистики за вчера для менеджера."""
        yesterday = (datetime.now() - timedelta(days=1)).date()
        start_of_day = datetime.combine(yesterday, datetime.min.time()).isoformat()
        end_of_day = datetime.combine(yesterday, datetime.max.time()).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT client_name, course, contract_amount, timestamp
                FROM closed_orders
                WHERE manager_id = ? AND timestamp BETWEEN ? AND ?
                ORDER BY timestamp DESC
            """,
                (manager_id, start_of_day, end_of_day),
            )
            return cursor.fetchall()

    def get_today_stats(self, manager_id: int) -> list:
        """Получение статистики за сегодня для менеджера."""
        today = datetime.now().date()
        start_of_day = datetime.combine(today, datetime.min.time()).isoformat()
        end_of_day = datetime.combine(today, datetime.max.time()).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT client_name, course, contract_amount, timestamp
                FROM closed_orders
                WHERE manager_id = ? AND timestamp BETWEEN ? AND ?
                ORDER BY timestamp DESC
            """,
                (manager_id, start_of_day, end_of_day),
            )
            return cursor.fetchall()

    def get_today_revenue_by_managers(self) -> dict:
        """
        Подсчитывает суммарную выручку (contract_amount) за сегодня для каждого менеджера.
        Возвращает словарь {manager_id: total_revenue}.
        """
        today = datetime.now().date()
        start_of_day = datetime.combine(today, datetime.min.time()).isoformat()
        end_of_day = datetime.combine(today, datetime.max.time()).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT DISTINCT manager_id
                FROM closed_orders
                WHERE timestamp BETWEEN ? AND ?
            """,
                (start_of_day, end_of_day),
            )
            manager_ids = [row[0] for row in cursor.fetchall()]

            revenue_by_manager = {}
            for manager_id in manager_ids:
                cursor.execute(
                    """
                    SELECT contract_amount
                    FROM closed_orders
                    WHERE manager_id = ? AND timestamp BETWEEN ? AND ?
                """,
                    (manager_id, start_of_day, end_of_day),
                )
                amounts = [
                    float(row[0])
                    for row in cursor.fetchall()
                    if row[0] and row[0].replace(".", "", 1).isdigit()
                ]
                total_revenue = sum(amounts) if amounts else 0.0
                revenue_by_manager[manager_id] = total_revenue

            return revenue_by_manager


stats_manager = StatsManager()
