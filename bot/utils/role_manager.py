import sqlite3
from typing import Optional


class RoleManager:
    def __init__(self, db_path: str = "users.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Инициализация базы данных с добавлением столбца is_active."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    telegram_id INTEGER PRIMARY KEY,
                    role TEXT NOT NULL,
                    is_active INTEGER DEFAULT 0
                )
            """
            )
            cursor.execute("PRAGMA table_info(users)")
            columns = [col[1] for col in cursor.fetchall()]
            if "is_active" not in columns:
                cursor.execute(
                    "ALTER TABLE users ADD COLUMN is_active INTEGER DEFAULT 0"
                )
            conn.commit()

    def add_user(self, telegram_id: int, role: str) -> bool:
        """Добавление пользователя с ролью, по умолчанию неактивен."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO users (telegram_id, role, is_active) VALUES (?, ?, 0)",
                (telegram_id, role),
            )
            conn.commit()
            return True

    def get_role(self, telegram_id: int) -> Optional[str]:
        """Получение роли пользователя."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT role FROM users WHERE telegram_id = ?", (telegram_id,)
            )
            result = cursor.fetchone()
            return result[0] if result else None

    def is_director(self, telegram_id: int) -> bool:
        return self.get_role(telegram_id) == "director"

    def is_manager(self, telegram_id: int) -> bool:
        return self.get_role(telegram_id) == "manager"

    def is_active(self, telegram_id: int) -> bool:
        """Проверка, активен ли пользователь."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT is_active FROM users WHERE telegram_id = ?", (telegram_id,)
            )
            result = cursor.fetchone()
            return bool(result[0]) if result else False

    def set_active(self, telegram_id: int, active: bool) -> bool:
        """Установка статуса активности."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE users SET is_active = ? WHERE telegram_id = ?",
                (1 if active else 0, telegram_id),
            )
            conn.commit()
            return True


role_manager = RoleManager()
