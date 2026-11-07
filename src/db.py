"""Phase 6: SQLite persistence for study tasks.

Teaching notes:
- sqlite3 is in the standard library (no extra dependency).
- We use parameterized queries (?) to prevent SQL injection.
- row_factory = sqlite3.Row lets us access columns by name.
- init_db() creates the table and seeds sample data if the table is empty.
- _reset_store() (test helper) deletes all rows.
"""

import datetime
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DB_PATH = PROJECT_ROOT / "data" / "tasks.db"

VALID_PRIORITIES = {"low", "medium", "high"}
VALID_STATUSES = {"pending", "done"}


def _now() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def get_conn() -> sqlite3.Connection:
    """Return a connection with Row factory for name-based column access."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def _row_to_dict(row: sqlite3.Row) -> dict:
    return {key: row[key] for key in row.keys()}


def init_db() -> None:
    """Create the tasks table and seed sample data if empty."""
    conn = get_conn()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            title       TEXT NOT NULL,
            course      TEXT,
            due_date    TEXT,
            priority    TEXT,
            status      TEXT,
            notes       TEXT,
            created_at  TEXT NOT NULL
        )
        """
    )
    conn.commit()
    count = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    if count == 0:
        _seed_samples(conn)
    conn.close()


def _seed_samples(conn: sqlite3.Connection) -> None:
    samples = [
        ("Study DBMS Chapter 5", "DBMS", "2026-11-10", "high", "pending", "Review normalization"),
        ("OS lab report", "OS", "2026-11-12", "medium", "pending", ""),
        ("Math problem set 4", "Math", "2026-11-14", "medium", "pending", ""),
    ]
    for title, course, due_date, priority, status, notes in samples:
        conn.execute(
            "INSERT INTO tasks (title, course, due_date, priority, status, notes, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (title, course, due_date, priority, status, notes, _now()),
        )
    conn.commit()


def reset_store() -> None:
    """Test helper: delete all rows (keeps table) and reset id counter."""
    conn = get_conn()
    conn.execute("DELETE FROM tasks")
    conn.execute("DELETE FROM sqlite_sequence WHERE name='tasks'")
    conn.commit()
    conn.close()


def insert_task(title: str, course: str, due_date: str,
                priority: str = "medium", notes: str = "") -> dict:
    conn = get_conn()
    cur = conn.execute(
        "INSERT INTO tasks (title, course, due_date, priority, status, notes, created_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (title, course, due_date, priority, "pending", notes, _now()),
    )
    conn.commit()
    task_id = cur.lastrowid
    conn.close()
    return get_task(task_id)


def get_task(task_id: int) -> dict | None:
    conn = get_conn()
    row = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    return _row_to_dict(row) if row else None


def list_tasks(status: str | None = None, course: str | None = None,
               limit: int = 20) -> list[dict]:
    conn = get_conn()
    query = "SELECT * FROM tasks"
    clauses = []
    params = []
    if status:
        clauses.append("status = ?")
        params.append(status)
    if course:
        clauses.append("course = ?")
        params.append(course)
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " LIMIT ?"
    params.append(limit)
    rows = conn.execute(query, params).fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def mark_done(task_id: int) -> dict | None:
    conn = get_conn()
    conn.execute("UPDATE tasks SET status = ? WHERE id = ?", ("done", task_id))
    conn.commit()
    conn.close()
    return get_task(task_id)


def update_task(task_id: int, **fields) -> dict | None:
    allowed = {"title", "course", "due_date", "priority", "status", "notes"}
    sets = []
    params = []
    for key, val in fields.items():
        if key in allowed:
            sets.append(f"{key} = ?")
            params.append(val)
    if not sets:
        return get_task(task_id)
    params.append(task_id)
    conn = get_conn()
    conn.execute(f"UPDATE tasks SET {', '.join(sets)} WHERE id = ?", params)
    conn.commit()
    conn.close()
    return get_task(task_id)


def delete_task(task_id: int) -> bool:
    conn = get_conn()
    cur = conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()
    conn.close()
    return cur.rowcount > 0


# Initialize on import so the table exists and sample data is seeded.
init_db()
