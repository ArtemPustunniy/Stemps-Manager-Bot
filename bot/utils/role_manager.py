import sqlite3
from typing import Optional


class RoleManager:
    def __init__(self, db_path: str = "users.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Инициализация базы данных и создание таблицы users."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    telegram_id INTEGER PRIMARY KEY,
                    role TEXT NOT NULL
                )
            """)
            conn.commit()

    def add_user(self, telegram_id: int, role: str) -> bool:
        """Добавление пользователя с ролью."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT OR REPLACE INTO users (telegram_id, role) VALUES (?, ?)", (telegram_id, role))
            conn.commit()
            return True

    def get_role(self, telegram_id: int) -> Optional[str]:
        """Получение роли пользователя по Telegram ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT role FROM users WHERE telegram_id = ?", (telegram_id,))
            result = cursor.fetchone()
            return result[0] if result else None

    def is_director(self, telegram_id: int) -> bool:
        return self.get_role(telegram_id) == "director"

    def is_manager(self, telegram_id: int) -> bool:
        return self.get_role(telegram_id) == "manager"


role_manager = RoleManager()

