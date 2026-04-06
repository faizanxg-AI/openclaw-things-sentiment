#!/usr/bin/env python3
"""Test emotion→sentiment mapping logic for things_sentiment_poller."""

import pytest
from datetime import datetime, timezone, timedelta
from things_sentiment_poller import (
    map_to_emotion,
    determine_sentiment,
    calculate_intensity,
    update_stats,
)

# Demo task templates covering all emotion categories
DEMO_TASKS = [
    # Positive emotions
    {
        "id": "demo_joy_1",
        "title": "Quick win: fixed the login bug",
        "project": "Today",
        "tags": ["quick"],
        "completionDate": datetime.now(timezone.utc).isoformat(),
        "creationDate": (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat(),
    },
    {
        "id": "demo_motivation_1",
        "title": "Finally launched the new feature",
        "project": "Inbox",
        "tags": [],
        "completionDate": datetime.now(timezone.utc).isoformat(),
        "creationDate": (datetime.now(timezone.utc) - timedelta(days=2)).isoformat(),
    },
    {
        "id": "demo_relief_1",
        "title": "Long overdue: tax filing completed",
        "project": "Logbook",
        "tags": ["overdue"],
        "completionDate": datetime.now(timezone.utc).isoformat(),
        "creationDate": (datetime.now(timezone.utc) - timedelta(days=30)).isoformat(),
    },
    {
        "id": "demo_anticipation_1",
        "title": "Planning next quarter roadmap",
        "project": "Upcoming",
        "tags": ["someday"],
        "completionDate": datetime.now(timezone.utc).isoformat(),
        "creationDate": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
    },
    # Negative emotions
    {
        "id": "demo_frustration_1",
        "title": "Overdue client presentation",
        "project": "Today",
        "tags": ["overdue", "urgent"],
        "completionDate": datetime.now(timezone.utc).isoformat(),
        "creationDate": (datetime.now(timezone.utc) - timedelta(days=10)).isoformat(),
    },
    {
        "id": "demo_stress_1",
        "title": "Urgent security patch",
        "project": "Inbox",
        "tags": ["urgent"],
        "completionDate": datetime.now(timezone.utc).isoformat(),
        "creationDate": (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat(),
    },
    # Neutral
    {
        "id": "demo_neutral_1",
        "title": "Routine maintenance",
        "project": "Logbook",
        "tags": ["routine"],
        "completionDate": datetime.now(timezone.utc).isoformat(),
        "creationDate": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
    },
]

@pytest.mark.unit
def test_demo_mapping():
    """Run mapping tests with demo tasks and verify outputs."""
    stats = {"total": 0, "very_positive": 0, "positive": 0, "neutral": 0, "negative": 0, "very_negative": 0}
    results = []

    for task in DEMO_TASKS:
        emotion, category = map_to_emotion(task)
        intensity = calculate_intensity(task, emotion)
        sentiment = determine_sentiment(emotion, intensity)
        update_stats(stats, sentiment)

        results.append({
            "task_id": task["id"],
            "title": task["title"],
            "emotion": emotion,
            "sentiment": sentiment,
            "intensity": intensity,
            "category": category,
        })

    # Assertions
    assert stats["total"] == len(DEMO_TASKS), "Total count mismatch"
    assert any(r["sentiment"] == "very_positive" for r in results), "Should have at least one very_positive"
    assert any(r["sentiment"] == "very_negative" for r in results), "Should have at least one very_negative"

    # Print results for manual verification (only shown with -s flag)
    print("\nTask Mapping Results (demo_mapping):")
    print("-" * 80)
    for r in results:
        print(f"{r['task_id']:25} | {r['emotion']:12} → {r['sentiment']:14} ({r['intensity']:.2f}) | {r['title'][:40]}")
    print("Stats:", stats)
