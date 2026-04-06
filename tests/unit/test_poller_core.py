"""Unit tests for things_sentiment_poller core functions with deterministic time control."""

import pytest
from datetime import datetime, timezone, timedelta
from things_sentiment_poller import (
    map_to_emotion,
    calculate_intensity,
    determine_sentiment,
    update_stats,
    iso_to_datetime,
    DELAY_DAYS,
)


class TestIsoToDatetime:
    """Test ISO8601 datetime parsing."""

    def test_valid_iso_with_z(self):
        iso = "2025-04-06T22:30:00Z"
        dt = iso_to_datetime(iso)
        assert dt is not None
        assert dt.tzinfo is not None

    def test_valid_iso_with_offset(self):
        iso = "2025-04-06T22:30:00+00:00"
        dt = iso_to_datetime(iso)
        assert dt is not None

    def test_none_input(self):
        assert iso_to_datetime(None) is None

    def test_empty_string(self):
        assert iso_to_datetime("") is None

    def test_invalid_iso(self):
        assert iso_to_datetime("not-a-date") is None


class TestMapToEmotion:
    """Test emotion mapping from task attributes."""

    def test_joy_from_quick_tag(self):
        task = {"title": "Fixed bug", "project": "", "tags": ["quick"], "area": ""}
        emotion, category = map_to_emotion(task)
        assert emotion == "joy"
        assert category == "Quick"

    def test_frustration_from_overdue_tag(self):
        task = {"title": "Late task", "project": "", "tags": ["overdue"], "area": ""}
        emotion, category = map_to_emotion(task)
        assert emotion == "frustration"

    def test_motivation_from_inbox(self):
        task = {"title": "Inbox task", "project": "inbox", "tags": [], "area": ""}
        emotion, category = map_to_emotion(task)
        assert emotion == "motivation"

    def test_motivation_from_today(self):
        task = {"title": "Today task", "project": "today", "tags": [], "area": ""}
        emotion, category = map_to_emotion(task)
        assert emotion == "motivation"

    def test_relief_from_logbook(self):
        task = {"title": "Logbook task", "project": "logbook", "tags": [], "area": ""}
        emotion, category = map_to_emotion(task)
        assert emotion == "relief"

    def test_relief_from_long_delay(self, emotion_boundary_tasks):
        """Test long-delayed completion triggers relief."""
        now = datetime.now(timezone.utc)
        task = {
            "id": "long_delay_test",
            "title": "Old task completed",
            "completionDate": now.isoformat(),
            "creationDate": (now - timedelta(days=30)).isoformat(),
        }
        emotion, category = map_to_emotion(task)
        assert emotion == "relief"
        assert category == "Long-delayed"

    def test_anticipation_from_upcoming(self):
        task = {"title": "Future task", "project": "upcoming", "tags": [], "area": ""}
        emotion, category = map_to_emotion(task)
        assert emotion == "anticipation"

    def test_anticipation_from_someday(self):
        task = {"title": "Someday task", "project": "someday", "tags": [], "area": ""}
        emotion, category = map_to_emotion(task)
        assert emotion == "anticipation"

    def test_neutral_fallback(self):
        task = {"title": "Unknown", "project": "Unknown", "tags": [], "area": ""}
        emotion, category = map_to_emotion(task)
        assert emotion == "neutral"
        assert category == "General"

    def test_tags_override_project(self):
        """Tags have priority over project-based emotion."""
        task = {"title": "Urgent inbox item", "project": "inbox", "tags": ["urgent"], "area": ""}
        emotion, category = map_to_emotion(task)
        # Urgent tag maps to stress via KEYWORD_EMOTIONS
        assert emotion == "stress"


class TestCalculateIntensity:
    """Test intensity calculation logic."""

    def test_joy_intensity(self):
        task = {"title": "Quick task", "tags": ["quick"]}
        intensity = calculate_intensity(task, "joy")
        assert intensity == 0.6

    def test_frustration_intensity(self):
        task = {"title": "Overdue", "tags": ["overdue"]}
        intensity = calculate_intensity(task, "frustration")
        assert intensity == 0.9

    def test_relief_intensity(self):
        task = {"title": "Completed old task"}
        intensity = calculate_intensity(task, "relief")
        assert intensity == 0.85

    def test_motivation_intensity(self):
        task = {"title": "Launch"}
        intensity = calculate_intensity(task, "motivation")
        assert intensity == 0.8

    def test_neutral_intensity(self):
        task = {"title": "Regular task"}
        intensity = calculate_intensity(task, "neutral")
        assert intensity == 0.5

    def test_unknown_emotion_falls_back_to_neutral(self):
        task = {"title": "Test"}
        intensity = calculate_intensity(task, "unknown_emotion")
        assert intensity == 0.5


class TestDetermineSentiment:
    """Test sentiment polarity mapping."""

    def test_very_positive_high_intensity(self):
        assert determine_sentiment("joy", 0.8) == "very_positive"
        assert determine_sentiment("motivation", 0.85) == "very_positive"
        assert determine_sentiment("relief", 0.9) == "very_positive"

    def test_positive_medium_intensity(self):
        assert determine_sentiment("joy", 0.6) == "positive"
        assert determine_sentiment("motivation", 0.7) == "positive"

    def test_neutral_low_intensity_positive(self):
        assert determine_sentiment("joy", 0.4) == "neutral"

    def test_very_negative_high_intensity(self):
        assert determine_sentiment("frustration", 0.9) == "very_negative"
        assert determine_sentiment("stress", 0.85) == "very_negative"

    def test_negative_medium_intensity(self):
        assert determine_sentiment("frustration", 0.7) == "negative"
        assert determine_sentiment("stress", 0.6) == "negative"

    def test_neutral_low_intensity_negative(self):
        assert determine_sentiment("stress", 0.4) == "neutral"

    def test_neutral_default(self):
        assert determine_sentiment("neutral", 0.5) == "neutral"
        assert determine_sentiment("unknown", 0.5) == "neutral"

    def test_without_intensity_positive(self):
        assert determine_sentiment("joy") == "positive"
        assert determine_sentiment("motivation") == "positive"

    def test_without_intensity_negative(self):
        assert determine_sentiment("frustration") == "negative"
        assert determine_sentiment("stress") == "negative"

    def test_without_intensity_neutral(self):
        assert determine_sentiment("neutral") == "neutral"


class TestUpdateStats:
    """Test stats tracking."""

    def test_increments_total(self):
        stats = {"total": 0}
        update_stats(stats, "positive")
        assert stats["total"] == 1

    def test_increments_sentiment_counters(self):
        stats = {"total": 0, "positive": 0, "neutral": 0}
        update_stats(stats, "positive")
        update_stats(stats, "neutral")
        assert stats["positive"] == 1
        assert stats["neutral"] == 1

    def test_unknown_sentiment_falls_back_to_neutral(self):
        stats = {"total": 0, "neutral": 0}
        update_stats(stats, "unknown_sentiment")
        assert stats["neutral"] == 1

    def test_all_sentiment_types(self):
        stats = {"total": 0, "very_positive": 0, "positive": 0, "neutral": 0, "negative": 0, "very_negative": 0}
        for sentiment in ["very_positive", "positive", "neutral", "negative", "very_negative"]:
            update_stats(stats, sentiment)
        assert stats["total"] == 5
        assert all(stats[s] == 1 for s in ["very_positive", "positive", "neutral", "negative", "very_negative"])


class TestBoundaryConditions:
    """Test edge cases and boundary conditions."""

    def test_empty_title(self):
        task = {"title": "", "project": "inbox", "tags": []}
        emotion, category = map_to_emotion(task)
        assert emotion == "motivation"

    def test_missing_project(self):
        task = {"title": "Task", "project": None, "tags": []}
        emotion, category = map_to_emotion(task)
        assert emotion == "neutral"  # Falls back to neutral

    def test_multiple_keyword_tags(self):
        task = {"title": "Urgent overdue task", "project": "", "tags": ["urgent", "overdue"]}
        emotion, category = map_to_emotion(task)
        # First matching tag in iteration order should win
        assert emotion in ["frustration", "stress"]

    def test_intensity_threshold_boundary(self):
        """Test behavior exactly at intensity thresholds."""
        # Test at exactly 0.6 boundary
        assert determine_sentiment("joy", 0.6) == "positive"
        assert determine_sentiment("joy", 0.599) == "neutral"

        # Test at exactly 0.8 boundary
        assert determine_sentiment("joy", 0.8) == "very_positive"
        assert determine_sentiment("joy", 0.799) == "positive"

        # Test negative thresholds
        assert determine_sentiment("stress", 0.6) == "negative"
        assert determine_sentiment("stress", 0.599) == "neutral"
        assert determine_sentiment("stress", 0.8) == "very_negative"

    def test_delay_threshold_boundary(self, now):
        """Test exactly at DELAY_DAYS boundary."""
        task = {
            "completionDate": now.isoformat(),
            "creationDate": (now - timedelta(days=DELAY_DAYS)).isoformat(),
        }
        emotion, category = map_to_emotion(task)
        # Exactly at threshold should not trigger relief (needs >=)
        # Actually checking the logic: duration.days >= DELAY_DAYS triggers relief
        assert emotion == "relief"

        # One day less
        task["creationDate"] = (now - timedelta(days=DELAY_DAYS - 1)).isoformat()
        emotion, category = map_to_emotion(task)
        assert emotion != "relief"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
