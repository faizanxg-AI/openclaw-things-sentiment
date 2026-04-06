"""Pytest configuration and shared fixtures for things_sentiment_poller."""

import json
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest

from things_sentiment_poller import (
    load_memory,
    load_state,
    save_state,
    iso_to_datetime,
    map_to_emotion,
    calculate_intensity,
    determine_sentiment,
    update_stats,
    CATEGORY_TO_EMOTION,
    KEYWORD_EMOTIONS,
    DELAY_DAYS,
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


@pytest.fixture
def sample_task(task_id="test_task_1", now=None):
    """Generate a sample Things task for testing."""
    if now is None:
        now = datetime.now(timezone.utc)

    return {
        "id": task_id,
        "title": "Test task",
        "project": "Inbox",
        "tags": [],
        "completionDate": now.isoformat(),
        "creationDate": (now - timedelta(days=1)).isoformat(),
    }


@pytest.fixture
def sample_tasks(count=5, now=None):
    """Generate multiple sample tasks with unique IDs."""
    if now is None:
        now = datetime.now(timezone.utc)

    tasks = []
    for i in range(count):
        tasks.append({
            "id": f"test_task_{i+1}",
            "title": f"Test task {i+1}",
            "project": "Inbox",
            "tags": [],
            "completionDate": now.isoformat(),
            "creationDate": (now - timedelta(days=i+1)).isoformat(),
        })
    return tasks


@pytest.fixture
def memory_file(temp_dir):
    """Create a temporary memory file path."""
    return temp_dir / "memory.json"


@pytest.fixture
def state_file(temp_dir):
    """Create a temporary state file path."""
    return temp_dir / "poller_state.json"


@pytest.fixture
def now():
    """Fixed current time for deterministic tests."""
    return datetime(2025, 4, 6, 12, 0, 0, tzinfo=timezone.utc)


@pytest.fixture
def empty_memory():
    """Return a fresh memory structure."""
    return {
        "sentiment_entries": [],
        "task_events": [],
        "stats": {"total": 0, "very_positive": 0, "positive": 0, "neutral": 0, "negative": 0, "very_negative": 0},
        "created_at": datetime.now(timezone.utc).isoformat()
    }


@pytest.fixture
def emotion_boundary_tasks(now=None):
    """Tasks designed to test emotion and intensity boundaries."""
    if now is None:
        now = datetime.now(timezone.utc)

    return [
        # Joy - high intensity (>0.6)
        {
            "id": "boundary_joy",
            "title": "Quick win: fixed the login bug",
            "project": "",
            "tags": ["quick"],
            "completionDate": now.isoformat(),
            "creationDate": (now - timedelta(hours=1)).isoformat(),
        },
        # Frustration - high intensity (>0.8)
        {
            "id": "boundary_frustration",
            "title": "Overdue client presentation",
            "project": "Today",
            "tags": ["overdue"],
            "completionDate": now.isoformat(),
            "creationDate": (now - timedelta(days=10)).isoformat(),
        },
        # Relief - long delay (>DELAY_DAYS)
        {
            "id": "boundary_relief",
            "title": "Tax filing completed",
            "project": "Logbook",
            "tags": [],
            "completionDate": now.isoformat(),
            "creationDate": (now - timedelta(days=30)).isoformat(),
        },
    ]


class MockNow:
    """Helper to mock current time for deterministic testing."""
    def __init__(self, now):
        self.now = now

    def __call__(self):
        return self.now
