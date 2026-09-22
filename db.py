"""Application data only. The Agents SDK owns its separate session database."""

import sqlite3
from contextlib import closing
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "app.db"


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DB_PATH, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def init_db() -> None:
    # PLACEHOLDER DATA: replace these tables and seeds after receiving the case.
    with closing(get_connection()) as connection, connection:
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS demo_items (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                value REAL NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY,
                text TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
        """)
        connection.executemany(
            "INSERT OR IGNORE INTO demo_items (id, name, value) VALUES (?, ?, ?)",
            [(1, "Demo Alpha", 12.5), (2, "Demo Beta", 8.0), (3, "Demo Gamma", 3.0)],
        )


def list_demo_items() -> list[dict]:
    with closing(get_connection()) as connection:
        return [dict(row) for row in connection.execute(
            "SELECT id, name, value, created_at FROM demo_items ORDER BY id"
        )]


def save_note(text: str) -> int:
    text = text.strip()
    if not text or len(text) > 2000:
        raise ValueError("A note must contain 1 to 2000 characters.")
    with closing(get_connection()) as connection, connection:
        cursor = connection.execute("INSERT INTO notes (text) VALUES (?)", (text,))
        return cursor.lastrowid
