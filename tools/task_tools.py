import json
import os
import uuid
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

TASKS_FILE = "data/tasks.json"

def _ensure_tasks_file():
    os.makedirs(os.path.dirname(TASKS_FILE), exist_ok=True)
    if not os.path.exists(TASKS_FILE):
        with open(TASKS_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)

def _load_tasks() -> List[Dict]:
    _ensure_tasks_file()
    try:
        with open(TASKS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load tasks: {e}")
        return []

def _save_tasks(tasks: List[Dict]):
    _ensure_tasks_file()
    try:
        with open(TASKS_FILE, "w", encoding="utf-8") as f:
            json.dump(tasks, f, indent=4)
    except Exception as e:
        logger.error(f"Failed to save tasks: {e}")

def add_task(title: str, description: str = "", scheduled_time: str = "") -> str:
    """Add a new task to the workflow list."""
    tasks = _load_tasks()
    task = {
        "id": str(uuid.uuid4())[:8],
        "title": title,
        "description": description,
        "scheduled_time": scheduled_time,
        "status": "pending"
    }
    tasks.append(task)
    _save_tasks(tasks)
    return f"Added task '{title}' with ID {task['id']}."

def list_tasks() -> str:
    """List all pending tasks."""
    tasks = [t for t in _load_tasks() if t.get("status") == "pending"]
    if not tasks:
        return "No pending tasks."
    
    output = []
    for t in tasks:
        sc = f" (Scheduled: {t.get('scheduled_time')})" if t.get('scheduled_time') else ""
        output.append(f"[{t['id']}] {t['title']}{sc}")
        if t.get('description'):
            output.append(f"    - {t['description']}")
    return "\n".join(output)

def mark_task_done(task_id: str) -> str:
    """Mark a task as completed by ID."""
    tasks = _load_tasks()
    for t in tasks:
        if t["id"] == task_id or task_id.lower() in t["title"].lower():
            if t["status"] == "pending":
                t["status"] = "completed"
                _save_tasks(tasks)
                return f"Marked task '{t['title']}' as completed."
            return f"Task '{t['title']}' was already completed."
    return f"Task with ID or name '{task_id}' not found."
