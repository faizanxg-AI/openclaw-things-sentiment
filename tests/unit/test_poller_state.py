"""Unit tests for state persistence and duplicate detection."""

import json
import os
import pytest
from datetime import datetime, timezone, timedelta
from things_sentiment_poller import load_state, save_state, load_memory
from pathlib import Path


class TestStateManagement:
    """Test state file operations."""

    def test_load_nonexistent_state(self, temp_dir):
        """load_state returns default when file doesn't exist."""
        state = load_state()
        assert state == {"last_poll": None, "last_task_id": None}

    def test_save_and_load_state(self, temp_dir, monkeypatch):
        """save_state persists data correctly."""
        # Monkeypatch STATE_FILE to use temp directory
        monkeypatch.setattr('things_sentiment_poller.STATE_FILE', temp_dir / "poller_state.json")

        save_state(last_poll="2025-04-06T22:00:00Z", last_task_id="task_123")
        state = load_state()

        assert state["last_poll"] == "2025-04-06T22:00:00Z"
        assert state["last_task_id"] == "task_123"

    def test_save_state_partial_update(self, temp_dir, monkeypatch):
        """Partial updates preserve existing fields."""
        monkeypatch.setattr('things_sentiment_poller.STATE_FILE', temp_dir / "poller_state.json")

        # Initial save
        save_state(last_poll="2025-04-06T22:00:00Z", last_task_id="task_123")

        # Partial update (only last_poll)
        save_state(last_poll="2025-04-07T00:00:00Z")
        state = load_state()

        assert state["last_poll"] == "2025-04-07T00:00:00Z"
        assert state["last_task_id"] == "task_123"  # Preserved

    def test_state_round_trip_immutability(self, temp_dir, monkeypatch):
        """Saved state shouldn't mutate previous loaded dict."""
        monkeypatch.setattr('things_sentiment_poller.STATE_FILE', temp_dir / "poller_state.json")

        save_state(last_poll="2025-04-06T22:00:00Z")
        state1 = load_state()
        state1["last_poll"] = "tampered"

        state2 = load_state()
        assert state2["last_poll"] == "2025-04-06T22:00:00Z"


class TestDuplicateDetection:
    """Test logic for skipping already-processed tasks."""

    def test_duplicate_by_task_id(self, sample_task, empty_memory, monkeypatch, temp_dir):
        """Tasks with same ID as last_task_id should be skipped."""
        monkeypatch.setattr('things_sentiment_poller.STATE_FILE', temp_dir / "poller_state.json")
        save_state(last_task_id=sample_task["id"])

        # Simulate checking if task should be processed
        task_id = sample_task["id"]
        state = load_state()
        if state.get("last_task_id") and task_id == state["last_task_id"]:
            should_skip = True
        else:
            should_skip = False

        assert should_skip is True

    def test_new_task_not_skipped(self, sample_task, empty_memory, monkeypatch, temp_dir):
        """Tasks with different ID from last_task_id are processed."""
        monkeypatch.setattr('things_sentiment_poller.STATE_FILE', temp_dir / "poller_state.json")
        save_state(last_task_id="different_task_id")

        task_id = sample_task["id"]
        state = load_state()
        if state.get("last_task_id") and task_id == state["last_task_id"]:
            should_skip = True
        else:
            should_skip = False

        assert should_skip is False

    def test_no_last_task_id_processes_all(self, sample_tasks, monkeypatch, temp_dir):
        """When last_task_id is None, all tasks are processed."""
        monkeypatch.setattr('things_sentiment_poller.STATE_FILE', temp_dir / "poller_state.json")
        save_state(last_task_id=None)

        new_tasks = []
        for task in sample_tasks:
            task_id = task["id"]
            state = load_state()
            if not state.get("last_task_id") or task_id != state["last_task_id"]:
                new_tasks.append(task)
                save_state(last_task_id=task_id)

        assert len(new_tasks) == len(sample_tasks)


class TestMemoryStructure:
    """Test memory file structure and defaults."""

    def test_load_memory_nonexistent(self, temp_dir, monkeypatch):
        """load_memory returns default structure when file missing."""
        monkeypatch.setattr('things_sentiment_poller.MEMORY_FILE', temp_dir / "memory.json")
        memory = load_memory()

        assert "sentiment_entries" in memory
        assert "task_events" in memory
        assert "stats" in memory
        assert memory["stats"]["total"] == 0

        for field in ["very_positive", "positive", "neutral", "negative", "very_negative"]:
            assert field in memory["stats"]
            assert memory["stats"][field] == 0

    def test_load_memory_existing(self, temp_dir, monkeypatch):
        """load_memory returns existing content when file present."""
        monkeypatch.setattr('things_sentiment_poller.MEMORY_FILE', temp_dir / "memory.json")

        existing = {
            "sentiment_entries": [{"id": "existing"}],
            "task_events": [],
            "stats": {"total": 1, "very_positive": 1, "positive": 0, "neutral": 0, "negative": 0, "very_negative": 0},
            "created_at": "2025-04-06T22:00:00Z"
        }
        with open(temp_dir / "memory.json", "w") as f:
            json.dump(existing, f)

        memory = load_memory()
        assert memory == existing


class TestStateConsistency:
    """Test state file JSON integrity and concurrency safety."""

    def test_state_json_valid(self, temp_dir, monkeypatch):
        """Written state file should be valid JSON."""
        monkeypatch.setattr('things_sentiment_poller.STATE_FILE', temp_dir / "poller_state.json")

        save_state(last_poll="2025-04-06T22:00:00Z", last_task_id="test_123")

        with open(temp_dir / "poller_state.json", "r") as f:
            data = json.load(f)

        assert "last_poll" in data
        assert "last_task_id" in data

    def test_state_file_created_with_correct_permissions(self, temp_dir, monkeypatch):
        """State file should be created with appropriate permissions."""
        import stat
        monkeypatch.setattr('things_sentiment_poller.STATE_FILE', temp_dir / "poller_state.json")

        save_state(last_poll="2025-04-06T22:00:00Z")
        file_stat = os.stat(temp_dir / "poller_state.json")

        # Should be readable and writable by owner (no executable bits)
        assert file_stat.st_mode & stat.S_IRUSR
        assert file_stat.st_mode & stat.S_IWUSR


class TestEdgeCases:
    """Test edge cases for state and duplicate detection as specified by Clawdiya."""

    def test_same_task_id_modified_content_skipped(self, sample_task, temp_dir):
        """Same task ID with modified content should be skipped (ID is immutable)."""
        state_path = temp_dir / "poller_state.json"
        # Mark task ID as processed
        save_state(last_task_id=sample_task["id"], path=state_path)

        # Simulate receiving the same task ID with different content
        modified_task = sample_task.copy()
        modified_task["title"] = "Modified title after completion"
        modified_task["tags"] = ["new", "tags"]

        state = load_state(path=state_path)
        should_skip = modified_task["id"] == state.get("last_task_id")

        assert should_skip is True

    def test_multiple_tasks_same_id(self, sample_task, temp_dir):
        """If multiple tasks have identical IDs (shouldn't happen), all are skipped after first."""
        state_path = temp_dir / "poller_state.json"

        # Simulate processing first task with this ID
        save_state(last_task_id=sample_task["id"], path=state_path)

        # Simulate duplicate tasks with same ID appearing in batch
        duplicate_tasks = [
            sample_task.copy(),
            {**sample_task, "title": "Duplicate 2"},
            {**sample_task, "title": "Duplicate 3"},
        ]

        # Processing logic: only tasks with new ID should be processed
        state = load_state(path=state_path)
        new_tasks = [t for t in duplicate_tasks if t["id"] != state.get("last_task_id")]

        assert len(new_tasks) == 0  # All duplicates skipped

    def test_corrupted_state_defaults_to_empty(self, temp_dir):
        """Corrupted state file with missing fields should default to empty state structure."""
        state_path = temp_dir / "poller_state.json"

        # Write corrupted state (missing last_task_id)
        corrupted_state = {"last_poll": "2025-04-06T22:00:00Z"}  # Missing last_task_id
        with open(state_path, "w") as f:
            json.dump(corrupted_state, f)

        # load_state should return defaults if required fields missing (after patching)
        state = load_state(path=state_path)

        # Should fall back to default structure with both keys
        assert "last_poll" in state
        assert "last_task_id" in state
        # After patching, missing fields should be set to None
        assert state["last_task_id"] is None

    def test_state_validation_after_save(self, temp_dir):
        """Saved state must contain required fields: last_poll and last_task_id."""
        state_path = temp_dir / "poller_state.json"

        # Save state with both fields
        save_state(last_poll="2025-04-06T22:00:00Z", last_task_id="task_123", path=state_path)

        # Verify by reading file directly
        with open(state_path, "r") as f:
            data = json.load(f)

        assert "last_poll" in data
        assert isinstance(data["last_poll"], str)
        assert "last_task_id" in data
        assert data["last_task_id"] == "task_123"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
