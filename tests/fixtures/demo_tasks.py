"""Reusable demo task fixtures for reproducible testing."""

from datetime import datetime, timezone, timedelta
import random

# Default base time for deterministic generation when base_time is not provided
_DEFAULT_BASE_TIME = datetime(2025, 1, 1, tzinfo=timezone.utc)


def generate_demo_tasks(seed=42, count=10, base_time=None):
    """Generate a deterministic set of demo tasks.

    For reproducibility, uses a fixed base_time if none provided.
    """
    rng = random.Random(seed)

    if base_time is None:
        base_time = _DEFAULT_BASE_TIME


    task_templates = [
        # Joy tasks
        {"title": "Quick win: fixed the login bug", "project": "Today", "tags": ["quick"]},
        {"title": "Deployed hotfix to production", "project": "Inbox", "tags": ["quick"]},
        {"title": "Completed code review in under 10min", "project": "Today", "tags": []},
        {"title": "Merged PR without conflicts", "project": "Inbox", "tags": ["quick"]},
        # Motivation tasks
        {"title": "Launched new feature after weeks", "project": "Inbox", "tags": []},
        {"title": "Delivered MVP to client", "project": "Today", "tags": []},
        {"title": "Ship it Friday release", "project": "Inbox", "tags": []},
        {"title": "Completed sprint goals early", "project": "Today", "tags": []},
        # Relief tasks (long-delayed)
        {"title": "Finally filed taxes", "project": "Logbook", "tags": [], "delay_days": 30},
        {"title": "Closed legacy issue from last year", "project": "Logbook", "tags": [], "delay_days": 365},
        {"title": "Completed annual compliance", "project": "Logbook", "tags": [], "delay_days": 90},
        # Anticipation tasks
        {"title": "Planned Q3 roadmap", "project": "Upcoming", "tags": []},
        {"title": "Sketched new product idea", "project": "Someday", "tags": []},
        {"title": "Researched upcoming tech", "project": "Upcoming", "tags": []},
        {"title": "Created wish list for next gen", "project": "Someday", "tags": []},
        # Frustration tasks
        {"title": "Overdue client presentation", "project": "Today", "tags": ["overdue"]},
        {"title": "Production outage fix", "project": "Inbox", "tags": ["urgent", "overdue"]},
        {"title": "Debugged CI pipeline failure", "project": "Inbox", "tags": ["urgent"]},
        {"title": "Resolved dependency conflict", "project": "Today", "tags": []},
        # Stress tasks
        {"title": "Last-minute regulatory report", "project": "Inbox", "tags": ["urgent"]},
        {"title": "Security patch before deadline", "project": "Inbox", "tags": ["urgent"]},
        {"title": "Emergency database migration", "project": "Today", "tags": []},
        # Neutral tasks
        {"title": "Routine maintenance", "project": "Logbook", "tags": ["routine"]},
        {"title": "Updated documentation", "project": "Inbox", "tags": []},
        {"title": "Weekly team sync", "project": "Today", "tags": []},
    ]

    # Shuffle deterministically
    shuffled = task_templates[:]
    rng.shuffle(shuffled)

    tasks = []
    for i, template in enumerate(shuffled[:count]):
        delay_days = template.get("delay_days", rng.randint(0, 5))
        creation_offset = timedelta(days=delay_days)

        task = {
            "id": f"demo_task_{i+1}",
            "title": template["title"],
            "project": template["project"],
            "tags": template["tags"][:],  # Copy list
            "area": "",
            "completionDate": base_time.isoformat(),
            "creationDate": (base_time - creation_offset).isoformat(),
        }
        tasks.append(task)

    return tasks


def generate_boundary_task(now, task_type="exact_threshold"):
    """
    Generate tasks specifically for testing intensity and threshold boundaries.

    Args:
        now: Reference datetime
        task_type: One of 'exact_threshold', 'just_below', 'just_above'

    Returns:
        Task dictionary with controlled attributes
    """
    if task_type == "exact_threshold":
        # Exactly at 0.6 intensity boundary for joy
        return {
            "id": "boundary_joy_0.6",
            "title": "Task with medium priority",
            "project": "Inbox",
            "tags": ["quick"],  # joy with 0.6 intensity
            "completionDate": now.isoformat(),
            "creationDate": (now - timedelta(hours=2)).isoformat(),
        }
    elif task_type == "just_below":
        # Just below 0.6
        return {
            "id": "boundary_joy_0.5",
            "title": "Simple completed task",
            "project": "Inbox",
            "tags": [],
            "completionDate": now.isoformat(),
            "creationDate": (now - timedelta(hours=2)).isoformat(),
        }
    elif task_type == "just_above":
        # Just above 0.8
        return {
            "id": "boundary_frustration_0.9",
            "title": "Overdue urgent task",
            "project": "Today",
            "tags": ["overdue", "urgent"],
            "completionDate": now.isoformat(),
            "creationDate": (now - timedelta(days=10)).isoformat(),
        }
