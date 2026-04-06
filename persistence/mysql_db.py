import os
import socket
import time
from pathlib import Path

import pymysql

_pool_kwargs: dict = {}
_conn: pymysql.Connection | None = None


def _read_secret(env_var: str, file_var: str) -> str | None:
    file_path = os.environ.get(file_var)
    if file_path:
        return Path(file_path).read_text().strip()
    return os.environ.get(env_var)


def _wait_for_port(host: str, port: int, timeout: float = 10.0):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1):
                return
        except OSError:
            time.sleep(0.5)
    raise TimeoutError(f"Could not connect to {host}:{port} within {timeout}s")


def _get_conn() -> pymysql.Connection:
    global _conn
    if _conn is None or not _conn.open:
        _conn = pymysql.connect(**_pool_kwargs)
    _conn.ping(reconnect=True)
    return _conn


def init():
    global _pool_kwargs
    host = _read_secret("MYSQL_HOST", "MYSQL_HOST_FILE")
    user = _read_secret("MYSQL_USER", "MYSQL_USER_FILE")
    password = _read_secret("MYSQL_PASSWORD", "MYSQL_PASSWORD_FILE")
    database = _read_secret("MYSQL_DB", "MYSQL_DB_FILE")

    _wait_for_port(host, 3306)

    _pool_kwargs = dict(
        host=host,
        user=user,
        password=password,
        database=database,
        charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )

    conn = _get_conn()
    with conn.cursor() as cur:
        cur.execute(
            "CREATE TABLE IF NOT EXISTS todo_items "
            "(id VARCHAR(36), name VARCHAR(255), completed BOOLEAN) "
            "DEFAULT CHARSET utf8mb4"
        )
    conn.commit()
    print(f"Connected to mysql db at host {host}")


def teardown():
    global _conn
    if _conn and _conn.open:
        _conn.close()
        _conn = None


def get_items() -> list[dict]:
    with _get_conn().cursor() as cur:
        cur.execute("SELECT * FROM todo_items")
        return [_row_to_dict(r) for r in cur.fetchall()]


def get_item(item_id: str) -> dict | None:
    with _get_conn().cursor() as cur:
        cur.execute("SELECT * FROM todo_items WHERE id=%s", (item_id,))
        row = cur.fetchone()
        return _row_to_dict(row) if row else None


def store_item(item: dict):
    conn = _get_conn()
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO todo_items (id, name, completed) VALUES (%s, %s, %s)",
            (item["id"], item["name"], 1 if item["completed"] else 0),
        )
    conn.commit()


def update_item(item_id: str, item: dict):
    conn = _get_conn()
    with conn.cursor() as cur:
        cur.execute(
            "UPDATE todo_items SET name=%s, completed=%s WHERE id=%s",
            (item["name"], 1 if item["completed"] else 0, item_id),
        )
    conn.commit()


def remove_item(item_id: str):
    conn = _get_conn()
    with conn.cursor() as cur:
        cur.execute("DELETE FROM todo_items WHERE id=%s", (item_id,))
    conn.commit()


def _row_to_dict(row: dict) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "completed": bool(row["completed"]),
    }
