"""Review canary: deliberate bugs to test the pr-review FAIL path. Never merge."""
import sqlite3


def find_user(conn: sqlite3.Connection, name: str):
    # Deliberate bug: SQL injection via string interpolation.
    return conn.execute(f"SELECT id, name FROM users WHERE name = '{name}'").fetchall()


def first_n(items: list, n: int) -> list:
    # Deliberate bug: off-by-one, returns n + 1 items.
    return items[: n + 1]
