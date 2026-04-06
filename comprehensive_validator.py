#!/usr/bin/env python3
"""Comprehensive validator for memory.json schema and data integrity."""

import json
import sys
from pathlib import Path
from datetime import datetime, timezone, timedelta

MEMORY_FILE = Path.home() / "agent-bridge" / "workspace" / "memory.json"

def validate_comprehensive():
    """Run all validation checks."""
    if not MEMORY_FILE.exists():
        print("memory.json does not exist")
        return False

    with open(MEMORY_FILE, 'r') as f:
        try:
            memory = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {e}")
            return False

    errors = []

    # Required top-level keys
    required_keys = ["sentiment_entries", "task_events", "stats", "created_at", "last_updated"]
    for key in required_keys:
        if key not in memory:
            errors.append(f"Missing required key: {key}")

    # Validate stats structure
    stats_keys = ["total", "very_positive", "positive", "neutral", "negative", "very_negative"]
    for key in stats_keys:
        if key not in memory["stats"]:
            errors.append(f"Missing stats key: {key}")
        elif not isinstance(memory["stats"][key], int):
            errors.append(f"Stats {key} must be integer")

    # Check stats counts match actual sentiment_entries bucket tallies
    actual_counts = {
        "very_positive": 0,
        "positive": 0,
        "neutral": 0,
        "negative": 0,
        "very_negative": 0
    }
    for entry in memory.get("sentiment_entries", []):
        sentiment = entry.get("sentiment")
        if sentiment in actual_counts:
            actual_counts[sentiment] += 1

    for sentiment in stats_keys[1:]:  # Skip total
        expected = memory["stats"].get(sentiment, 0)
        actual = actual_counts[sentiment]
        if expected != actual:
            errors.append(f"Stats {sentiment}: expected {expected}, actual {actual}")

    # Validate total matches sum of buckets
    total_expected = sum(actual_counts.values())
    if memory["stats"].get("total", 0) != total_expected:
        errors.append(f"Stats total: expected {total_expected}, actual {memory['stats'].get('total')}")

    # Validate timestamps
    try:
        created_at = datetime.fromisoformat(memory["created_at"].replace("Z", "+00:00"))
        last_updated = datetime.fromisoformat(memory["last_updated"].replace("Z", "+00:00"))
    except ValueError as e:
        errors.append(f"Invalid timestamp format: {e}")

    # Check all timestamps are within last 14 days (for demo)
    now = datetime.now(timezone.utc)
    fourteen_days_ago = now - timedelta(days=14)

    for entry in memory.get("sentiment_entries", []):
        # Check description field present and non-empty
        if "description" not in entry:
            errors.append(f"Entry {entry.get('task_id', 'unknown')}: missing description")
        elif not entry["description"].strip():
            errors.append(f"Entry {entry.get('task_id', 'unknown')}: description is empty")

        # Validate timestamp
        try:
            entry_ts_str = entry["timestamp"].replace("Z", "+00:00")
            entry_ts = datetime.fromisoformat(entry_ts_str)
            if entry_ts < fourteen_days_ago:
                errors.append(f"Entry {entry.get('task_id', 'unknown')}: timestamp too old ({entry_ts})")
        except (ValueError, KeyError) as e:
            errors.append(f"Entry {entry.get('task_id', 'unknown')}: invalid timestamp: {e}")

    # Check for duplicate task_ids
    task_ids = [entry["task_id"] for entry in memory.get("sentiment_entries", []) if "task_id" in entry]
    if len(task_ids) != len(set(task_ids)):
        duplicates = [tid for tid in task_ids if task_ids.count(tid) > 1]
        errors.append(f"Duplicate task_ids found: {set(duplicates)}")

    if errors:
        print("VALIDATION FAILED:")
        for error in errors:
            print(f"  ✗ {error}")
        return False

    print("✓ All comprehensive validation checks passed")
    return True

if __name__ == "__main__":
    success = validate_comprehensive()
    sys.exit(0 if success else 1)
