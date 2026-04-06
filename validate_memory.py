#!/usr/bin/env python3
"""Validate memory.json schema compliance."""

import json
import sys
from pathlib import Path
from datetime import datetime

MEMORY_FILE = Path.home() / "agent-bridge" / "workspace" / "memory.json"

def validate_memory():
    """Assert memory.json structure matches expected schema."""
    if not MEMORY_FILE.exists():
        print("memory.json does not exist")
        return False

    with open(MEMORY_FILE, 'r') as f:
        try:
            memory = json.load(f)
        except json.JSONDecodeError as e:
            print(f"Invalid JSON: {e}")
            return False

    # Required top-level keys
    required_keys = ["sentiment_entries", "task_events", "stats", "created_at", "last_updated"]
    for key in required_keys:
        if key not in memory:
            print(f"Missing required key: {key}")
            return False

    # Validate stats structure
    stats_keys = ["total", "very_positive", "positive", "neutral", "negative", "very_negative"]
    for key in stats_keys:
        if key not in memory["stats"]:
            print(f"Missing stats key: {key}")
            return False
        if not isinstance(memory["stats"][key], int):
            print(f"Stats {key} must be integer")
            return False

    # Validate timestamp format
    try:
        datetime.fromisoformat(memory["created_at"].replace("Z", "+00:00"))
        datetime.fromisoformat(memory["last_updated"].replace("Z", "+00:00"))
    except ValueError:
        print("Invalid timestamp format")
        return False

    # Validate sentiment_entries structure
    for entry in memory["sentiment_entries"]:
        entry_fields = ["timestamp", "source", "task_id", "title", "category", "emotion", "sentiment", "intensity", "tags", "description"]
        for field in entry_fields:
            if field not in entry:
                print(f"Missing entry field: {field}")
                return False

        # Validate sentiment value
        valid_sentiments = ["very_positive", "positive", "neutral", "negative", "very_negative"]
        if entry["sentiment"] not in valid_sentiments:
            print(f"Invalid sentiment: {entry['sentiment']}")
            return False

        # Validate intensity range
        if not 0.0 <= entry["intensity"] <= 1.0:
            print(f"Invalid intensity: {entry['intensity']}")
            return False

        # Validate tags is list
        if not isinstance(entry["tags"], list):
            print("tags must be a list")
            return False

    print("✓ Memory schema validation passed")
    return True

if __name__ == "__main__":
    success = validate_memory()
    sys.exit(0 if success else 1)
