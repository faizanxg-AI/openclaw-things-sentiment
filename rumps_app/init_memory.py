#!/usr/bin/env python3
"""Initialize memory.json with proper structure."""

from pathlib import Path
import json
from datetime import datetime

MEMORY_FILE = Path.home() / "agent-bridge" / "workspace" / "memory.json"

def init_memory():
    data = {
        "sentiment_entries": [],
        "task_events": [],
        "stats": {
            "total": 0,
            "very_positive": 0,
            "positive": 0,
            "neutral": 0,
            "negative": 0,
            "very_negative": 0
        },
        "created_at": datetime.now().isoformat()
    }
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(MEMORY_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    print(f"Initialized memory at {MEMORY_FILE}")

if __name__ == "__main__":
    init_memory()