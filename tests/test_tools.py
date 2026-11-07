"""Phase 2: pure unit tests for tools (no LLM, no network)."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import tools  # noqa: E402


def setup_function():
    tools._reset_store()


def test_add_task_success():
    res = tools.add_task("Study DBMS Ch5", "DBMS", "2026-11-10", "high")
    assert "task" in res
    assert res["task"]["id"] == 1
    assert res["task"]["status"] == "pending"
    assert res["task"]["title"] == "Study DBMS Ch5"


def test_add_task_validation():
    assert "error" in tools.add_task("", "DBMS", "2026-11-10")
    assert "error" in tools.add_task("x", "DBMS", "2026-11-10", "urgent")


def test_list_tasks_filter():
    tools.add_task("A", "DBMS", "2026-11-10")
    tools.add_task("B", "OS", "2026-11-11")
    tools.mark_task_done(1)
    assert tools.list_tasks()["count"] == 2
    assert tools.list_tasks(status="done")["count"] == 1
    assert tools.list_tasks(course="OS")["count"] == 1


def test_mark_task_done():
    tools.add_task("A", "DBMS", "2026-11-10")
    res = tools.mark_task_done(1)
    assert res["task"]["status"] == "done"
    assert tools.list_tasks(status="pending")["count"] == 0


def test_mark_task_done_not_found():
    assert "error" in tools.mark_task_done(999)


def test_registry():
    assert set(tools.TOOLS_BY_NAME) == {
        "add_task", "list_tasks", "mark_task_done", "get_task",
        "update_task", "delete_task",
    }
    assert len(tools.TOOLS_SCHEMA) == 6
    for schema in tools.TOOLS_SCHEMA:
        assert "name" in schema and "parameters" in schema


def test_get_task():
    tools._reset_store()
    tools.add_task("A", "DBMS", "2026-11-10")
    assert tools.get_task(1)["task"]["title"] == "A"
    assert "error" in tools.get_task(999)
