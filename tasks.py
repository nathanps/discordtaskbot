from __future__ import annotations

import csv
import os
from datetime import date
from dataclasses import dataclass, asdict, fields
from typing import Optional

from config import get_csv_path, STATES


@dataclass
class Task:
    id: int
    task_name: str
    author: str
    assignee: str
    date_created: str
    state: str
    category: str
    notes: str


FIELDNAMES = [f.name for f in fields(Task)]


def _read_tasks(csv_path: str) -> list[Task]:
    """Read all tasks from CSV."""
    if not os.path.exists(csv_path):
        return []

    with open(csv_path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return [Task(**row) for row in reader]


def _write_tasks(csv_path: str, tasks: list[Task]) -> None:
    """Write all tasks to CSV."""
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for task in tasks:
            writer.writerow(asdict(task))


def _get_next_id(tasks: list[Task]) -> int:
    """Get next available ID (max + 1, never reuses)."""
    if not tasks:
        return 1
    return max(int(t.id) for t in tasks) + 1


def add_task(guild_id: int, task_name: str, author: str, category: str = "") -> Task:
    """Add a new task and return it."""
    csv_path = get_csv_path(guild_id)
    tasks = _read_tasks(csv_path)
    new_task = Task(
        id=_get_next_id(tasks),
        task_name=task_name,
        author=author,
        assignee="",
        date_created=date.today().isoformat(),
        state="open",
        category=category,
        notes=""
    )
    tasks.append(new_task)
    _write_tasks(csv_path, tasks)
    return new_task


def get_task(guild_id: int, task_id: int) -> Optional[Task]:
    """Get a task by ID."""
    csv_path = get_csv_path(guild_id)
    tasks = _read_tasks(csv_path)
    for task in tasks:
        if int(task.id) == task_id:
            return task
    return None


def get_tasks(
    guild_id: int,
    state_filter: Optional[str] = None,
    category_filter: Optional[str] = None,
    assignee_filter: Optional[str] = None,
    include_done: bool = False,
    limit: int = 15
) -> list[Task]:
    """
    Get filtered list of tasks.

    Args:
        guild_id: Discord guild/server ID
        state_filter: Filter by specific state ("open", "in-progress", "done", "all")
        category_filter: Filter by category
        assignee_filter: Filter by assignee username
        include_done: Include done tasks (used when state_filter is None)
        limit: Maximum number of tasks to return
    """
    csv_path = get_csv_path(guild_id)
    tasks = _read_tasks(csv_path)

    # Filter by state
    if state_filter == "all":
        pass  # No filtering
    elif state_filter == "done":
        tasks = [t for t in tasks if t.state == "done"]
    elif state_filter in STATES:
        tasks = [t for t in tasks if t.state == state_filter]
    else:
        # Default: open + in-progress only
        if not include_done:
            tasks = [t for t in tasks if t.state in ("open", "in-progress")]

    # Filter by category
    if category_filter and category_filter not in ("all", "done"):
        tasks = [t for t in tasks if t.category.lower() == category_filter.lower()]

    # Filter by assignee
    if assignee_filter:
        tasks = [t for t in tasks if t.assignee.lower() == assignee_filter.lower()]

    # Respect CSV order, apply limit
    return tasks[:limit]


def update_task_state(guild_id: int, task_id: int, new_state: str) -> Optional[Task]:
    """Update task state. Returns updated task or None if not found."""
    if new_state not in STATES:
        return None

    csv_path = get_csv_path(guild_id)
    tasks = _read_tasks(csv_path)
    for task in tasks:
        if int(task.id) == task_id:
            task.state = new_state
            _write_tasks(csv_path, tasks)
            return task
    return None


def assign_task(guild_id: int, task_id: int, assignee: str) -> Optional[Task]:
    """Assign task to user. Returns updated task or None if not found."""
    csv_path = get_csv_path(guild_id)
    tasks = _read_tasks(csv_path)
    for task in tasks:
        if int(task.id) == task_id:
            task.assignee = assignee
            _write_tasks(csv_path, tasks)
            return task
    return None


def add_note(guild_id: int, task_id: int, note: str) -> Optional[Task]:
    """Add note to task. Appends to existing notes."""
    csv_path = get_csv_path(guild_id)
    tasks = _read_tasks(csv_path)
    for task in tasks:
        if int(task.id) == task_id:
            if task.notes:
                task.notes = f"{task.notes} | {note}"
            else:
                task.notes = note
            _write_tasks(csv_path, tasks)
            return task
    return None


def delete_task(guild_id: int, task_id: int) -> bool:
    """Delete task by ID. Returns True if deleted, False if not found."""
    csv_path = get_csv_path(guild_id)
    tasks = _read_tasks(csv_path)
    original_len = len(tasks)
    tasks = [t for t in tasks if int(t.id) != task_id]

    if len(tasks) < original_len:
        _write_tasks(csv_path, tasks)
        return True
    return False
