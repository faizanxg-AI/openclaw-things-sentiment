#!/usr/bin/env python3
"""
Health check script for the polling service.
Returns 0 if healthy, 1 if unhealthy.
"""

import json
import sys
from pathlib import Path

STATUS_FILE = Path("polling_status.json")

def check_health():
    """Check if polling service is healthy."""
    if not STATUS_FILE.exists():
        print("❌ Status file not found")
        return 1

    try:
        with open(STATUS_FILE) as f:
            status = json.load(f)

        # Check if service is running (last update recent)
        last_update = status.get("last_update")
        if not last_update:
            print("❌ No last_update timestamp")
            return 1

        # Could add time threshold check here if desired
        print(f"✅ Polling service healthy. Last update: {last_update}")
        print(f"   Total tasks processed: {status.get('total_tasks', 0)}")
        print(f"   Latest sentiment: {status.get('latest_sentiment', 'n/a')}")
        return 0
    except json.JSONDecodeError as e:
        print(f"❌ Invalid status file: {e}")
        return 1
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(check_health())
