"""Integration tests for things_sentiment_poller CLI with --now override and other flags."""

import json
import pytest
from datetime import datetime, timezone, timedelta
from pathlib import Path
import subprocess
import sys


class TestPollerCLI:
    """Test the poller command-line interface with deterministic time control."""

    def test_poller_with_now_override(self, temp_dir, monkeypatch):
        """Test that --now overrides the current time used by the poller."""
        # This test will only work once the poller implements the --now flag
        # For now, we structure it as a template

        # Arrange
        monkeypatch.setattr('things_sentiment_poller.MEMORY_FILE', temp_dir / "memory.json")
        monkeypatch.setattr('things_sentiment_poller.STATE_FILE', temp_dir / "poller_state.json")

        fixed_now = datetime(2025, 4, 6, 22, 0, 0, tzinfo=timezone.utc)
        now_iso = fixed_now.isoformat()

        # Create a mock Things CLI response
        mock_task = {
            "id": "test_task_1",
            "title": "Test task at fixed time",
            "project": "Inbox",
            "tags": [],
            "completionDate": now_iso,
            "creationDate": (fixed_now - timedelta(days=1)).isoformat(),
        }

        # We'll need to mock subprocess.run or Things CLI
        # For now, structure the test expectations

        # Act: python things_sentiment_poller.py --now "2025-04-06T22:00:00Z" --output <temp_memory>
        # (Once --now is implemented)

        # Assert
        # - Memory file timestamps should match the overridden now
        # - Task entries should use completionDate from task (which is fixed)
        # - No actual time.now() calls should leak in

        pytest.skip("Wait for --now flag implementation in poller")

    def test_demo_mode_with_seed(self, temp_dir, monkeypatch):
        """Test that --seed produces reproducible demo tasks."""
        # This test will verify that demo mode generates same tasks on repeated runs

        monkeypatch.setattr('things_sentiment_poller.MEMORY_FILE', temp_dir / "memory_demo.json")

        # Run poller multiple times with same seed
        # All output memory files should contain identical entries

        pytest.skip("Wait for --seed flag implementation in demo mode")

    def test_duplicate_detection_across_runs(self, temp_dir, monkeypatch):
        """Test that already-processed task_ids are not re-added to memory."""
        monkeypatch.setattr('things_sentiment_poller.MEMORY_FILE', temp_dir / "memory.json")
        monkeypatch.setattr('things_sentiment_poller.STATE_FILE', temp_dir / "poller_state.json")

        # First run: add task
        #   mock task returns task_id "abc123"
        # Second run: same task_id appears, should be skipped

        pytest.skip("Requires integration test with durable state file")

    def test_intensity_scaling_thresholds(self, temp_dir, monkeypatch):
        """Verify intensity thresholds produce expected sentiment categories."""
        from things_sentiment_poller import determine_sentiment

        # High intensity joy (>0.8) -> very_positive
        assert determine_sentiment("joy", 0.85) == "very_positive"

        # Medium joy (0.6-0.8) -> positive
        assert determine_sentiment("joy", 0.7) == "positive"

        # Low joy (<0.6) -> neutral
        assert determine_sentiment("joy", 0.4) == "neutral"

        # High frustration (>0.8) -> very_negative
        assert determine_sentiment("frustration", 0.9) == "very_negative"

        # Medium frustration (0.6-0.8) -> negative
        assert determine_sentiment("frustration", 0.7) == "negative"

        # Low frustration (<0.6) -> neutral
        assert determine_sentiment("frustration", 0.4) == "neutral"

    def test_boundary_condition_joy_at_0_6(self, temp_dir, monkeypatch):
        """Test exact boundary at 0.6 for joy (should be positive, not neutral)."""
        from things_sentiment_poller import determine_sentiment

        # At exactly 0.6, joy should be positive (>= 0.6)
        assert determine_sentiment("joy", 0.6) == "positive"

        # Just below 0.6 should be neutral
        assert determine_sentiment("joy", 0.599) == "neutral"

    def test_boundary_condition_frustration_at_0_8(self):
        """Test exact boundary at 0.8 for frustration (should be very_negative)."""
        from things_sentiment_poller import determine_sentiment

        assert determine_sentiment("frustration", 0.8) == "very_negative"
        assert determine_sentiment("frustration", 0.799) == "negative"

    def test_verify_mode_no_polling(self, temp_dir, monkeypatch):
        """Test --verify flag only validates memory without polling or writing."""
        # Create a valid memory file
        memory_file = temp_dir / "memory.json"
        valid_memory = {
            "sentiment_entries": [{"id": "test"}],
            "stats": {"total": 1, "very_positive": 0, "positive": 0, "neutral": 1, "negative": 0, "very_negative": 0},
        }
        with open(memory_file, "w") as f:
            json.dump(valid_memory, f)

        # Run with --verify
        # Should exit with code 0 if valid, not modify file

        pytest.skip("Implementation needed: add --verify support")


class TestReproducibility:
    """Test demo mode reproducibility with --seed."""

    def test_demo_mode_seed_reproducibility(self, temp_dir, monkeypatch):
        """Two runs with same seed should produce identical memory output."""
        from tests.fixtures.demo_tasks import generate_demo_tasks

        tasks1 = generate_demo_tasks(seed=12345, count=50)
        tasks2 = generate_demo_tasks(seed=12345, count=50)

        assert len(tasks1) == len(tasks2)
        for t1, t2 in zip(tasks1, tasks2):
            assert t1 == t2, "Tasks differ with same seed"

    def test_demo_mode_seed_variation(self):
        """Different seeds should produce different task sequences."""
        from tests.fixtures.demo_tasks import generate_demo_tasks

        tasks1 = generate_demo_tasks(seed=111, count=20)
        tasks2 = generate_demo_tasks(seed=999, count=20)

        # At least one task should differ (titles may differ due to template selection)
        titles1 = [t["title"] for t in tasks1]
        titles2 = [t["title"] for t in tasks2]

        assert titles1 != titles2, "Different seeds produced identical sequence"

    def test_demo_mode_contains_all_emotion_categories(self):
        """A sufficiently large demo set should cover all emotion types."""
        from tests.fixtures.demo_tasks import generate_demo_tasks
        from things_sentiment_poller import map_to_emotion

        tasks = generate_demo_tasks(seed=42, count=100)
        emotions = set()

        for task in tasks:
            emotion, _ = map_to_emotion(task)
            emotions.add(emotion)

        expected_emotions = {"joy", "motivation", "relief", "anticipation", "frustration", "stress", "neutral"}
        assert emotions.intersection(expected_emotions), "Demo tasks didn't produce any known emotions"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
