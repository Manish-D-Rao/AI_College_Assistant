"""Phase 2: study-task tools as plain Python functions + MANUAL JSON schemas.
"""

import datetime

_TASKS = []
_NEXT_ID = 1

VALID_PRIORITIES = {"low", "medium", "high"}
VALID_STATUSES = {"pending", "done"}


def _now() -> str:
    return datetime.datetime.now().isoformat(timespec="seconds")


def _reset_store() -> None:
    global _TASKS, _NEXT_ID
    _TASKS = []
    _NEXT_ID = 1


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
    global _NEXT_ID
    if not title or not title.strip():
        return {"error": "title is required"}
    if priority not in VALID_PRIORITIES:
        return {"error": f"priority must be one of {sorted(VALID_PRIORITIES)}"}
    task = {
        "id": _NEXT_ID,
        "title": title.strip(),
        "course": course,
        "due_date": due_date,
        "priority": priority,
        "status": "pending",
        "notes": notes,
        "created_at": _now(),
    }
    _TASKS.append(task)
    _NEXT_ID += 1
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
    results = list(_TASKS)
    if status:
        results = [t for t in results if t["status"] == status]
    if course:
        results = [t for t in results if t["course"] == course]
    return {"tasks": results[:limit], "count": len(results)}


def mark_task_done(task_id: int) -> dict:
    """Mark a study task as done by its id.

    Args:
        task_id (int): The id of the task to complete.

    Returns:
        dict: {"task": {...}} on success, {"error": "..."} if not found.
    """
    for task in _TASKS:
        if task["id"] == task_id:
            task["status"] = "done"
            return {"task": task}
    return {"error": f"task {task_id} not found"}


def get_task(task_id: int) -> dict:
    """Fetch a single study task by its id.

    Args:
        task_id (int): The id of the task.

    Returns:
        dict: {"task": {...}} on success, {"error": "..."} if not found.
    """
    for task in _TASKS:
        if task["id"] == task_id:
            return {"task": task}
    return {"error": f"task {task_id} not found"}


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

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
TOOLS = {
    "add_task": {"handler": add_task, "declaration": add_task_schema},
    "list_tasks": {"handler": list_tasks, "declaration": list_tasks_schema},
    "mark_task_done": {"handler": mark_task_done, "declaration": mark_task_done_schema},
    "get_task": {"handler": get_task, "declaration": get_task_schema},
}
TOOLS_BY_NAME = {name: info["handler"] for name, info in TOOLS.items()}
TOOLS_SCHEMA = [info["declaration"] for info in TOOLS.values()]


if __name__ == "__main__":
    _reset_store()
    print(add_task("Study DBMS Chapter 5", "DBMS", "2026-11-10", "high"))
    print(add_task("OS lab report", "OS", "2026-11-12"))
    print(get_task(1))
    print(list_tasks())
    print(mark_task_done(1))
    print(list_tasks(status="done"))
