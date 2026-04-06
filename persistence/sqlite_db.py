import os
import sqlite3
from pathlib import Path

LOCATION = os.environ.get("SQLITE_DB_LOCATION", "/etc/todos/todo.db")
_conn: sqlite3.Connection | None = None


def _get_conn() -> sqlite3.Connection:
    assert _conn is not None, "Database not initialised — call init() first"
    return _conn


def init():
    global _conn
    Path(LOCATION).parent.mkdir(parents=True, exist_ok=True)
    _conn = sqlite3.connect(LOCATION, check_same_thread=False)
    _conn.row_factory = sqlite3.Row
    _conn.execute(
        "CREATE TABLE IF NOT EXISTS todo_items "
        "(id VARCHAR(36), name VARCHAR(255), completed BOOLEAN)"
    )
    _conn.commit()
    print(f"Using sqlite database at {LOCATION}")


def teardown():
    global _conn
    if _conn:
        _conn.close()
        _conn = None


def get_items() -> list[dict]:
    rows = _get_conn().execute("SELECT * FROM todo_items").fetchall()
    return [_row_to_dict(r) for r in rows]


def get_item(item_id: str) -> dict | None:
    row = _get_conn().execute(
        "SELECT * FROM todo_items WHERE id=?", (item_id,)
    ).fetchone()
    return _row_to_dict(row) if row else None


def store_item(item: dict):
    _get_conn().execute(
        "INSERT INTO todo_items (id, name, completed) VALUES (?, ?, ?)",
        (item["id"], item["name"], 1 if item["completed"] else 0),
    )
    _get_conn().commit()


def update_item(item_id: str, item: dict):
    _get_conn().execute(
        "UPDATE todo_items SET name=?, completed=? WHERE id=?",
        (item["name"], 1 if item["completed"] else 0, item_id),
    )
    _get_conn().commit()


def remove_item(item_id: str):
    _get_conn().execute("DELETE FROM todo_items WHERE id=?", (item_id,))
    _get_conn().commit()


def _row_to_dict(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "completed": bool(row["completed"]),
    }
