"""Phase 2/6: study-task tools backed by SQLite (via db.py).

Teaching notes (read top-down):
- Tools are ordinary Python functions; they now delegate to src/db.py (SQLite).
- Each function validates input and returns a dict: {"task": ...} or {"error": ...}.
  Returning errors (not raising) lets the LLM see failures and recover.
- _reset_store(): test helper (clears all rows).
- Schemas (add_task_schema, ...): hand-written JSON "menu" the LLM reads.
- Registry: TOOLS (name->{handler,declaration}), TOOLS_BY_NAME (execute), TOOLS_SCHEMA (advertise).
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

import db

VALID_PRIORITIES = {"low", "medium", "high"}
VALID_STATUSES = {"pending", "done"}


def _reset_store() -> None:
    """Test helper: clear all rows in the tasks table."""
    db.reset_store()


def add_task(title: str, course: str, due_date: str,
             priority: str = "medium", notes: str = "") -> dict:
    """Create a new study task and return it.

    Args:
        title (str): Short title of the task.
        course (str): Course name, e.g. "DBMS".
        due_date (str): Due date in YYYY-MM-DD.
        priority (str): One of low, medium, high.
        notes (str): Optional extra notes.

    Returns:
        dict: {"task": {...}} on success, {"error": "..."} on failure.
    """
    if not title or not title.strip():
        return {"error": "title is required"}
    if priority not in VALID_PRIORITIES:
        return {"error": f"priority must be one of {sorted(VALID_PRIORITIES)}"}
    task = db.insert_task(title.strip(), course, due_date, priority, notes)
    return {"task": task}


def list_tasks(status: str | None = None, course: str | None = None,
               limit: int = 20) -> dict:
    """List study tasks, optionally filtered by status or course.

    Args:
        status (str | None): Filter by "pending" or "done".
        course (str | None): Filter by course name.
        limit (int): Max number of tasks to return.

    Returns:
        dict: {"tasks": [...], "count": N}.
    """
    if status and status not in VALID_STATUSES:
        return {"error": f"status must be one of {sorted(VALID_STATUSES)}"}
    tasks = db.list_tasks(status=status, course=course, limit=limit)
    return {"tasks": tasks, "count": len(tasks)}


def mark_task_done(task_id: int) -> dict:
    """Mark a study task as done by its id.

    Args:
        task_id (int): The id of the task to complete.

    Returns:
        dict: {"task": {...}} on success, {"error": "..."} if not found.
    """
    task = db.get_task(task_id)
    if task is None:
        return {"error": f"task {task_id} not found"}
    updated = db.mark_done(task_id)
    return {"task": updated}


def get_task(task_id: int) -> dict:
    """Fetch a single study task by its id.

    Args:
        task_id (int): The id of the task.

    Returns:
        dict: {"task": {...}} on success, {"error": "..."} if not found.
    """
    task = db.get_task(task_id)
    if task is None:
        return {"error": f"task {task_id} not found"}
    return {"task": task}


def update_task(task_id: int, **fields) -> dict:
    """Update fields of a study task.

    Args:
        task_id (int): The id of the task.
        **fields: title, course, due_date, priority, status, notes.

    Returns:
        dict: {"task": {...}} on success, {"error": "..."} if not found.
    """
    task = db.get_task(task_id)
    if task is None:
        return {"error": f"task {task_id} not found"}
    if "priority" in fields and fields["priority"] not in VALID_PRIORITIES:
        return {"error": f"priority must be one of {sorted(VALID_PRIORITIES)}"}
    if "status" in fields and fields["status"] not in VALID_STATUSES:
        return {"error": f"status must be one of {sorted(VALID_STATUSES)}"}
    updated = db.update_task(task_id, **fields)
    return {"task": updated}


def delete_task(task_id: int) -> dict:
    """Delete a study task by its id.

    Args:
        task_id (int): The id of the task.

    Returns:
        dict: {"deleted": True} on success, {"error": "..."} if not found.
    """
    task = db.get_task(task_id)
    if task is None:
        return {"error": f"task {task_id} not found"}
    ok = db.delete_task(task_id)
    return {"deleted": ok}


# ---------------------------------------------------------------------------
# Manual JSON schemas
# ---------------------------------------------------------------------------
add_task_schema = {
    "name": "add_task",
    "description": "Create a new study task for the student.",
    "parameters": {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Short title of the task."},
            "course": {"type": "string", "description": "Course name, e.g. DBMS."},
            "due_date": {"type": "string", "description": "Due date in YYYY-MM-DD."},
            "priority": {
                "type": "string",
                "description": "low, medium, or high.",
                "enum": ["low", "medium", "high"],
            },
            "notes": {"type": "string", "description": "Optional extra notes."},
        },
        "required": ["title", "course", "due_date"],
    },
}

list_tasks_schema = {
    "name": "list_tasks",
    "description": "List the student's study tasks, optionally filtered.",
    "parameters": {
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "description": "Filter by status: pending or done.",
                "enum": ["pending", "done"],
            },
            "course": {"type": "string", "description": "Filter by course name."},
            "limit": {"type": "integer", "description": "Max tasks to return."},
        },
        "required": [],
    },
}

mark_task_done_schema = {
    "name": "mark_task_done",
    "description": "Mark a study task as completed by its id.",
    "parameters": {
        "type": "object",
        "properties": {
            "task_id": {"type": "integer", "description": "The id of the task."},
        },
        "required": ["task_id"],
    },
}

get_task_schema = {
    "name": "get_task",
    "description": "Fetch a single study task by its id.",
    "parameters": {
        "type": "object",
        "properties": {
            "task_id": {"type": "integer", "description": "The id of the task."},
        },
        "required": ["task_id"],
    },
}

update_task_schema = {
    "name": "update_task",
    "description": "Update fields of a study task by its id.",
    "parameters": {
        "type": "object",
        "properties": {
            "task_id": {"type": "integer", "description": "The id of the task."},
            "title": {"type": "string", "description": "New title."},
            "course": {"type": "string", "description": "New course."},
            "due_date": {"type": "string", "description": "New due date YYYY-MM-DD."},
            "priority": {"type": "string", "enum": ["low", "medium", "high"]},
            "status": {"type": "string", "enum": ["pending", "done"]},
            "notes": {"type": "string", "description": "New notes."},
        },
        "required": ["task_id"],
    },
}

delete_task_schema = {
    "name": "delete_task",
    "description": "Delete a study task by its id.",
    "parameters": {
        "type": "object",
        "properties": {
            "task_id": {"type": "integer", "description": "The id of the task."},
        },
        "required": ["task_id"],
    },
}

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
TOOLS = {
    "add_task": {"handler": add_task, "declaration": add_task_schema},
    "list_tasks": {"handler": list_tasks, "declaration": list_tasks_schema},
    "mark_task_done": {"handler": mark_task_done, "declaration": mark_task_done_schema},
    "get_task": {"handler": get_task, "declaration": get_task_schema},
    "update_task": {"handler": update_task, "declaration": update_task_schema},
    "delete_task": {"handler": delete_task, "declaration": delete_task_schema},
}
TOOLS_BY_NAME = {name: info["handler"] for name, info in TOOLS.items()}
TOOLS_SCHEMA = [info["declaration"] for info in TOOLS.values()]


if __name__ == "__main__":
    _reset_store()
    print(add_task("Study DBMS Chapter 5", "DBMS", "2026-11-10", "high"))
    print(list_tasks())
    print(mark_task_done(1))
