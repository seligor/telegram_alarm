import sqlite3
from typing import Optional, List, Tuple


def init_db():
    conn = sqlite3.connect('alarm_bot.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        group_id TEXT
    )
    ''')

    conn.commit()
    conn.close()


def add_user(user_id: int, username: str, group_id: str):
    conn = sqlite3.connect('alarm_bot.db')
    cursor = conn.cursor()

    cursor.execute('''
    INSERT OR REPLACE INTO users (user_id, username, group_id)
    VALUES (?, ?, ?)
    ''', (user_id, username, group_id))

    conn.commit()
    conn.close()


def get_users_in_group(group_id: str) -> List[Tuple[int, str]]:
    conn = sqlite3.connect('alarm_bot.db')
    cursor = conn.cursor()

    cursor.execute('''
    SELECT user_id, username FROM users WHERE group_id = ?
    ''', (group_id,))

    users = cursor.fetchall()
    conn.close()
    return users


def get_user_group(user_id: int) -> Optional[str]:
    conn = sqlite3.connect('alarm_bot.db')
    cursor = conn.cursor()

    cursor.execute('''
    SELECT group_id FROM users WHERE user_id = ?
    ''', (user_id,))

    result = cursor.fetchone()
    conn.close()
    return result[0] if result else None
