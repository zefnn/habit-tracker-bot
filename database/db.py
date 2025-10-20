import sqlite3
from datetime import datetime, date


class Database:
    def __init__(self, db_path: str = "habits.db"):
        self.db_path = db_path
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        user_id INTEGER PRIMARY KEY,
                        username TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)

        cursor.execute("""
                    CREATE TABLE IF NOT EXISTS habits (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        user_id INTEGER NOT NULL,
                        name TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users(user_id)
                    )
                """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS completions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                habit_id INTEGER NOT NULL,
                completed_at DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (habit_id) REFERENCES habit(id),
                UNIQUE (habit_id, completed_at)
            )
        """)

        conn.commit()
        conn.close()

    def add_user(self, user_id: int, username: str):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username)
        )

        conn.commit()
        conn.close()

    def add_habit(self, user_id: int, habit_name: str):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO habits (user_id, name) VALUES (?, ?)
        """, (user_id, habit_name))

        conn.commit()
        conn.close()

    def get_all_habits(self, user_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, name, created_at FROM habits
            WHERE user_id = ?
            ORDER BY created_at
        """, (user_id,))

        habits = cursor.fetchall()
        conn.close()

        return [(row[0], row[1], row[2]) for row in habits]


    def mark_habit_done(self, habit_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT OR IGNORE INTO completions (habit_id, completed_at) VALUES (?, ?)
        """, (habit_id, date.today().isoformat()))

        conn.commit()
        conn.close()

    def mark_habit_not_done(self, habit_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        today = date.today().isoformat()
        cursor.execute("""
            DELETE FROM completions
            WHERE habit_id = ? AND completed_at = ?
        """, (habit_id, today))

        conn.commit()
        conn.close()

    def is_habit_done_today(self, habit_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()

        today = date.today().isoformat()

        cursor.execute("""
            SELECT COUNT(*) FROM completions
            WHERE habit_id = ? AND completed_at = ?
        """, (habit_id, today))

        count = cursor.fetchone()[0]
        cursor.close()
        return count > 0


    def delete_habit(self, habit_id: int, user_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            DELETE FROM habits
            WHERE id = ? AND user_id = ?
        """, (habit_id, user_id))

        cursor.execute("""
            DELETE FROM completions
            WHERE habit_id = ?
        """, (habit_id, ))

        conn.commit()
        conn.close()