"""
Task storage module providing in-memory CRUD operations with optional JSON file persistence.

This module uses:
- A module-level dictionary to store tasks keyed by integer IDs.
- Auto-incrementing integer IDs starting at 1.
- Optional persistence to data/tasks.json when PERSIST_TO_FILE environment variable is set to a truthy value.
- Atomic writes to avoid partial file corruption.
- Safe directory creation for the persistence file path.

PUBLIC INTERFACE:
- list_tasks() -> list[dict]
- create_task(title: str) -> dict
- update_task(task_id: int, data: dict) -> dict | None
- delete_task(task_id: int) -> bool
- get_task(task_id: int) -> dict | None
"""

import json
import os
import tempfile
from typing import Dict, List, Optional, Tuple

# Module-level in-memory store and ID counter
_TASKS: Dict[int, Dict] = {}
_NEXT_ID: int = 1

# Persistence configuration
_PERSIST_ENV_VAR = "PERSIST_TO_FILE"
# Relative to backend root; path resolved at runtime from CWD
_PERSIST_PATH = os.path.join("data", "tasks.json")


def _env_truthy(value: Optional[str]) -> bool:
    """Return True for typical truthy env var strings."""
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _should_persist() -> bool:
    """Check if persistence is enabled via environment variable."""
    return _env_truthy(os.getenv(_PERSIST_ENV_VAR))


def _ensure_dir_exists(path: str) -> None:
    """Ensure the directory for the given path exists."""
    directory = os.path.dirname(path)
    if directory:
        os.makedirs(directory, exist_ok=True)


def _atomic_write_json(path: str, data: dict) -> None:
    """
    Atomically write JSON data to the given path.

    Writes to a temporary file in the same directory and then renames it,
    ensuring that the resulting file is either the old complete file or
    the new complete file.
    """
    _ensure_dir_exists(path)
    dir_name = os.path.dirname(path) or "."
    fd, tmp_path = tempfile.mkstemp(prefix=".tmp_tasks_", dir=dir_name, text=True)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp_file:
            json.dump(data, tmp_file, ensure_ascii=False, indent=2)
            tmp_file.flush()
            os.fsync(tmp_file.fileno())
        # On POSIX, rename is atomic. On Windows, replace semantics also work.
        os.replace(tmp_path, path)
    finally:
        # Cleanup temp file if something went wrong before replace
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            # Best-effort cleanup only
            pass


def _load_from_file(path: str) -> Tuple[Dict[int, Dict], int]:
    """
    Load tasks and next_id from JSON file if it exists and is valid.

    Returns:
        A tuple (tasks_dict, next_id_value).
    """
    if not os.path.exists(path):
        return {}, 1

    try:
        with open(path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        tasks_list = payload.get("tasks", [])
        # Build dict keyed by id and compute next_id
        tasks: Dict[int, Dict] = {}
        max_id = 0
        for t in tasks_list:
            # Validate and coerce task shape
            if not isinstance(t, dict):
                continue
            tid = t.get("id")
            title = t.get("title")
            completed = t.get("completed", False)
            if not isinstance(tid, int):
                continue
            if not isinstance(title, str):
                continue
            if not isinstance(completed, bool):
                completed = bool(completed)
            tasks[tid] = {"id": tid, "title": title, "completed": completed}
            if tid > max_id:
                max_id = tid
        next_id = max_id + 1 if max_id >= 1 else 1
        return tasks, next_id
    except Exception:
        # If file is corrupt or unreadable, start fresh in-memory
        return {}, 1


def _save_to_file(path: str, tasks: Dict[int, Dict], next_id: int) -> None:
    """Persist tasks and next_id to disk atomically if persistence is enabled."""
    if not _should_persist():
        return
    payload = {
        "tasks": list(tasks.values()),
        "next_id": next_id,
        "version": 1,
    }
    _atomic_write_json(path, payload)


def _initialize() -> None:
    """Initialize store from file if persistence is enabled."""
    global _TASKS, _NEXT_ID
    if _should_persist():
        tasks, next_id = _load_from_file(_PERSIST_PATH)
        _TASKS = tasks
        _NEXT_ID = next_id


# Initialize store on module import
_initialize()


# PUBLIC_INTERFACE
def list_tasks() -> List[Dict]:
    """
    List all tasks currently stored.

    Returns:
        A list of task dicts with shape: {"id": int, "title": str, "completed": bool}.
    """
    # Return a shallow copy list to avoid external mutation
    return list(_TASKS.values())


# PUBLIC_INTERFACE
def create_task(title: str) -> Dict:
    """
    Create a new task with the given title.

    Args:
        title: The title of the task.

    Returns:
        The created task dict: {"id": int, "title": str, "completed": bool}.
    """
    global _NEXT_ID
    if not isinstance(title, str) or not title.strip():
        raise ValueError("title must be a non-empty string")

    task = {"id": _NEXT_ID, "title": title.strip(), "completed": False}
    _TASKS[_NEXT_ID] = task
    _NEXT_ID += 1

    _save_to_file(_PERSIST_PATH, _TASKS, _NEXT_ID)
    return task


# PUBLIC_INTERFACE
def update_task(task_id: int, data: Dict) -> Optional[Dict]:
    """
    Update an existing task by id.

    Args:
        task_id: The task ID to update.
        data: Dict with optional keys: "title" (str), "completed" (bool).

    Returns:
        The updated task dict if found, else None.
    """
    task = _TASKS.get(task_id)
    if task is None:
        return None

    if "title" in data:
        title = data["title"]
        if title is None:
            # Ignore None; cannot set to None
            pass
        else:
            if not isinstance(title, str) or not title.strip():
                raise ValueError("title must be a non-empty string")
            task["title"] = title.strip()

    if "completed" in data:
        completed = data["completed"]
        if isinstance(completed, bool):
            task["completed"] = completed
        else:
            # Attempt to coerce common truthy/falsy representations
            if isinstance(completed, str):
                task["completed"] = completed.strip().lower() in {"1", "true", "yes", "on"}
            else:
                task["completed"] = bool(completed)

    _TASKS[task_id] = task
    _save_to_file(_PERSIST_PATH, _TASKS, _NEXT_ID)
    return task


# PUBLIC_INTERFACE
def delete_task(task_id: int) -> bool:
    """
    Delete a task by id.

    Args:
        task_id: The task ID to delete.

    Returns:
        True if the task was deleted, False if not found.
    """
    removed = _TASKS.pop(task_id, None) is not None
    if removed:
        _save_to_file(_PERSIST_PATH, _TASKS, _NEXT_ID)
    return removed


# PUBLIC_INTERFACE
def get_task(task_id: int) -> Optional[Dict]:
    """
    Retrieve a single task by id.

    Args:
        task_id: The task ID to retrieve.

    Returns:
        The task dict if found, else None.
    """
    return _TASKS.get(task_id)
