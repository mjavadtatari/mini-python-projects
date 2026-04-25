import sqlite3
from pathlib import Path

DB_NAME = "app.db"


def get_db_path() -> Path:
    return Path(__file__).resolve().parent.parent / DB_NAME


def get_connection() -> sqlite3.Connection:
    db_path = get_db_path()
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection
