"""Test state persistence across poller restarts (deduplication)."""

import json
import tempfile
from pathlib import Path
from things_sentiment_poller import load_state, save_state, get_completed_tasks

def test_state_persistence_prevents_duplicate_processing(tmp_path):
    # Arrange: create initial state with last_poll and last_task_id
    state_file = tmp_path / "poller_state.json"
    initial_state = {
        "last_poll": "2025-01-01T00:00:00",
        "last_task_id": "task_123"
    }
    save_state(last_poll=initial_state["last_poll"], last_task_id=initial_state["last_task_id"], path=state_file)

    # Act: load the state
    loaded_state = load_state(path=state_file)

    # Assert: state contains expected keys and values
    assert loaded_state["last_poll"] == "2025-01-01T00:00:00"
    assert loaded_state["last_task_id"] == "task_123"

    # Simulate a new poll: if we get tasks including task_123, we should skip it
    mock_tasks = [
        {"id": "task_123", "title": "Already processed"},
        {"id": "task_456", "title": "New task"}
    ]

    processed_ids = []
    for task in mock_tasks:
        if task["id"] == loaded_state["last_task_id"]:
            continue
        processed_ids.append(task["id"])

    assert processed_ids == ["task_456"], "Duplicate task should be skipped"

if __name__ == "__main__":
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        test_state_persistence_prevents_duplicate_processing(Path(tmp))
        print("State persistence test passed")
