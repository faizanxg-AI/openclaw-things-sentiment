#!/usr/bin/env python3
"""
Poll Things 3 completed tasks and map to sentiment entries.

Features:
- Tag-first emotion mapping (keywords override project)
- Intensity-based sentiment (very_positive/very_negative thresholds)
- Duplicate detection via poller_state.json
- Demo mode with reproducible tasks (--demo --seed)
- Verification mode (--verify)
- Custom output (--output)
- Deterministic testing (--now ISO8601)
- Auto-copy to memory.json with --use-demo
"""

import argparse
import json
import random
import string
import subprocess
import sys
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path

def iso_to_datetime(iso_str: str) -> datetime:
    """Parse ISO8601 string and return timezone-aware datetime.
    Attaches UTC if the string is naive (no tzinfo).
    """
    s = iso_str.replace("Z", "+00:00")
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt

# Configuration defaults
WORKSPACE = Path.home() / "agent-bridge" / "workspace"
MEMORY_FILE = WORKSPACE / "memory.json"
STATE_FILE = WORKSPACE / "poller_state.json"
THINGS_CMD = "things"
POLL_LIMIT = 100

# Intensity thresholds
INTENSITY_VERY_HIGH = 0.8
INTENSITY_HIGH = 0.6
INTENSITY_MEDIUM = 0.4

# Emotion constants
EMOTION_JOY = "joy"
EMOTION_MOTIVATION = "motivation"
EMOTION_GRATITUDE = "gratitude"
EMOTION_FRUSTRATION = "frustration"
EMOTION_FATIGUE = "fatigue"
EMOTION_CALM = "calm"
EMOTION_RELIEF = "relief"
EMOTION_ANTICIPATION = "anticipation"
EMOTION_STRESS = "stress"
EMOTION_NEUTRAL = "neutral"

# Sentiment buckets
SENTIMENT_VERY_POSITIVE = "very_positive"
SENTIMENT_POSITIVE = "positive"
SENTIMENT_NEUTRAL = "neutral"
SENTIMENT_NEGATIVE = "negative"
SENTIMENT_VERY_NEGATIVE = "very_negative"

# Categories
CATEGORY_QUICK = "Quick"
CATEGORY_LONG_DELAYED = "Long-delayed"
CATEGORY_OVERDUE = "Overdue"
CATEGORY_INBOX = "Inbox"
CATEGORY_TODAY = "Today"
CATEGORY_LOGBOOK = "Logbook"
CATEGORY_UPCOMING = "Upcoming"
CATEGORY_GENERAL = "General"

# Mappings
KEYWORD_EMOTIONS = {
    "overdue": EMOTION_FRUSTRATION,
    "urgent": EMOTION_STRESS,
    "quick": EMOTION_JOY,
    "trivial": EMOTION_JOY,
    "routine": EMOTION_NEUTRAL,
    "deep": EMOTION_MOTIVATION,
    "focus": EMOTION_MOTIVATION,
}

CATEGORY_TO_EMOTION = {
    CATEGORY_QUICK: EMOTION_JOY,
    CATEGORY_LONG_DELAYED: EMOTION_RELIEF,
    CATEGORY_INBOX: EMOTION_MOTIVATION,
    CATEGORY_TODAY: EMOTION_MOTIVATION,
    CATEGORY_LOGBOOK: EMOTION_RELIEF,
    CATEGORY_UPCOMING: EMOTION_ANTICIPATION,
    CATEGORY_GENERAL: EMOTION_NEUTRAL,
}


# Time thresholds (days)
DELAY_DAYS = 7
BOUNDARY_24H_HOURS = 24

def load_memory(path=None):
    """Load memory with full schema defaults."""
    if path is None:
        path = MEMORY_FILE
    if path.exists():
        with open(path, 'r') as f:
            return json.load(f)
    return {
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
        "created_at": datetime.now(timezone.utc).isoformat(),
        "last_updated": datetime.now(timezone.utc).isoformat()
    }

def load_state(path=None):
    """Load poller state (last_poll, last_task_id)."""
    if path is None:
        path = STATE_FILE
    if path.exists():
        try:
            with open(path, 'r') as f:
                state = json.load(f)
        except json.JSONDecodeError:
            state = {}
    else:
        state = {}
    # Ensure required keys exist
    state.setdefault("last_poll", None)
    state.setdefault("last_task_id", None)
    return state


def save_state(*, last_poll=None, last_task_id=None, path=None):
    """Save poller state with optional updates."""
    if path is None:
        path = STATE_FILE
    # Load existing state if available to preserve unspecified fields
    if path.exists():
        with open(path, 'r') as f:
            state = json.load(f)
    else:
        state = {"last_poll": None, "last_task_id": None}
    if last_poll is not None:
        state["last_poll"] = last_poll
    if last_task_id is not None:
        state["last_task_id"] = last_task_id
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(state, f, indent=2)


def save_memory(memory, path=MEMORY_FILE):
    memory["last_updated"] = datetime.now(timezone.utc).isoformat()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(memory, f, indent=2)

def update_stats(stats, sentiment):
    """Increment stats for a sentiment bucket."""
    valid = [SENTIMENT_VERY_POSITIVE, SENTIMENT_POSITIVE, SENTIMENT_NEUTRAL,
             SENTIMENT_NEGATIVE, SENTIMENT_VERY_NEGATIVE]
    # Ensure all valid keys exist
    for key in valid:
        if key not in stats:
            stats[key] = 0
    if sentiment not in valid:
        sentiment = SENTIMENT_NEUTRAL
    stats[sentiment] += 1
    stats["total"] = sum(stats[key] for key in valid)


def get_completed_tasks(since=None, limit=POLL_LIMIT, things_cmd=THINGS_CMD):
    """Fetch completed tasks from Things CLI."""
    cmd = [things_cmd, "completed", "--json", "--limit", str(limit)]
    if since:
        cmd.extend(["--modified-after", since])
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error calling Things: {result.stderr}", file=sys.stderr)
        return []
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}", file=sys.stderr)
        return []

def generate_demo_tasks(seed=42, now=None, count=10):
    """Generate synthetic tasks covering all emotion paths and edge cases."""
    rnd = random.Random(seed)
    if now is None:
        now = datetime.now(timezone.utc)
    tasks = []
    # Predefined templates for diversity
    templates = [
        # Positive
        {"title": "Quick win: fixed the login bug", "project": "Today", "tags": ["quick"], "emotion": "joy"},
        {"title": "Finally launched the new feature", "project": "Inbox", "tags": [], "emotion": "motivation"},
        {"title": "Long overdue: tax filing completed", "project": "Logbook", "tags": ["overdue"], "emotion": "relief"},
        {"title": "Planning next quarter roadmap", "project": "Upcoming", "tags": ["someday"], "emotion": "anticipation"},
        # Negative
        {"title": "Overdue client presentation", "project": "Today", "tags": ["overdue", "urgent"], "emotion": "frustration"},
        {"title": "Urgent security patch", "project": "Inbox", "tags": ["urgent"], "emotion": "stress"},
        # Neutral
        {"title": "Routine maintenance", "project": "Logbook", "tags": ["routine"], "emotion": "neutral"},
        # Edge: missing tags, placeholder title (empty not allowed), long description
        {"title": "(Untitled task)", "project": "Inbox", "tags": [], "emotion": "neutral"},
        {"title": "Deep work session: multiple paragraphs\n\nSecond paragraph with details and more context to simulate a real task description that is longer than usual.", "project": "Today", "tags": ["deep", "focus"], "emotion": "motivation"},
        # Boundary: exactly 24h and 7d
        {"title": "Exactly 24h ago: on-time task", "project": "Today", "tags": [], "emotion": "motivation", "age_hours": 24},
        {"title": "Exactly 7 days ago: long-delayed completion", "project": "Logbook", "tags": [], "emotion": "relief", "age_days": 7},
    ]
    for i in range(count):
        tpl = rnd.choice(templates)
        # Determine completion timestamp based on age hints or random recent
        if "age_hours" in tpl:
            comp_time = now - timedelta(hours=tpl["age_hours"])
        elif "age_days" in tpl:
            comp_time = now - timedelta(days=tpl["age_days"])
        else:
            # Random within last 14 days
            days_ago = rnd.uniform(0, 14)
            comp_time = now - timedelta(days=days_ago)
        # Build task dict
        task = {
            "id": f"demo_{i}_{uuid.uuid4().hex[:8]}",
            "title": tpl["title"],
            "project": tpl["project"],
            "tags": tpl["tags"],
            "completionDate": comp_time.isoformat(),
            "creationDate": (comp_time - timedelta(hours=rnd.uniform(1, 168))).isoformat(),
        }
        tasks.append(task)
    return tasks

def map_to_emotion(task) -> tuple[str, str]:
    """Tag-first emotion mapping with category inference."""
    title = (task.get("title") or "").lower()
    tags = [t.lower() for t in (task.get("tags") or [])]
    project = (task.get("project") or "").lower()

    # 1. Keyword overrides
    if "overdue" in tags or "overdue" in title:
        # Check for long-delayed completion as additional signal
        comp_str = task.get("completionDate")
        creation_str = task.get("creationDate")
        if comp_str and creation_str:
            comp = iso_to_datetime(comp_str)
            creation = iso_to_datetime(creation_str)
            if comp is not None and creation is not None:
                if (comp - creation).days >= DELAY_DAYS:
                    return EMOTION_RELIEF, CATEGORY_LONG_DELAYED
        return EMOTION_FRUSTRATION, CATEGORY_OVERDUE
    if "urgent" in tags:
        return EMOTION_STRESS, CATEGORY_GENERAL
    if "quick" in tags or "trivial" in tags:
        return EMOTION_JOY, CATEGORY_QUICK
    if "routine" in tags:
        return EMOTION_NEUTRAL, CATEGORY_GENERAL
    if "deep" in tags or "focus" in tags:
        return EMOTION_MOTIVATION, CATEGORY_GENERAL

    # 2. Date-based long-delayed (if not already returned)
    comp_str = task.get("completionDate")
    creation_str = task.get("creationDate")
    if comp_str and creation_str:
        comp = iso_to_datetime(comp_str)
        creation = iso_to_datetime(creation_str)
        if comp is not None and creation is not None:
            if (comp - creation).days >= DELAY_DAYS:
                return EMOTION_RELIEF, CATEGORY_LONG_DELAYED

    # 3. Project-based defaults
    if project in ("inbox", "today"):
        category = CATEGORY_INBOX if project == "inbox" else CATEGORY_TODAY
        return EMOTION_MOTIVATION, category
    if project == "logbook":
        return EMOTION_RELIEF, CATEGORY_LOGBOOK
    if project in ("upcoming", "someday"):
        return EMOTION_ANTICIPATION, CATEGORY_UPCOMING

    # 4. Fallback
    return EMOTION_NEUTRAL, CATEGORY_GENERAL




def calculate_intensity(task=None, emotion=None, now=None) -> float:
    """Deterministic intensity mapping per test spec.
    Accepts either (emotion) or (task, emotion). Returns a fixed float per emotion.
    """
    intensity_map = {
        EMOTION_JOY: INTENSITY_HIGH,
        EMOTION_MOTIVATION: 0.8,
        EMOTION_RELIEF: 0.85,
        EMOTION_FRUSTRATION: 0.9,
        EMOTION_STRESS: 0.9,
        EMOTION_ANTICIPATION: INTENSITY_MEDIUM,
        EMOTION_NEUTRAL: 0.5,
    }
    # Handle legacy single-arg call: calculate_intensity("joy")
    if task is not None and emotion is None:
        emotion = task
    if emotion is None:
        raise ValueError("emotion is required")
    return intensity_map.get(emotion, 0.5)




def determine_sentiment(emotion, intensity=None) -> str:
    """Map emotion+intensity to 5-tier sentiment."""
    emotion = emotion.lower() if isinstance(emotion, str) else ""
    positive_emotions = [EMOTION_JOY, EMOTION_MOTIVATION, EMOTION_RELIEF, EMOTION_ANTICIPATION]
    negative_emotions = [EMOTION_FRUSTRATION, EMOTION_STRESS]

    if intensity is None:
        if emotion in positive_emotions:
            return SENTIMENT_POSITIVE
        if emotion in negative_emotions:
            return SENTIMENT_NEGATIVE
        return SENTIMENT_NEUTRAL

    intensity = max(0.0, min(1.0, intensity))
    if emotion in positive_emotions:
        if intensity >= INTENSITY_VERY_HIGH:
            return SENTIMENT_VERY_POSITIVE
        elif intensity >= INTENSITY_HIGH:
            return SENTIMENT_POSITIVE
        else:
            return SENTIMENT_NEUTRAL
    elif emotion in negative_emotions:
        if intensity >= INTENSITY_VERY_HIGH:
            return SENTIMENT_VERY_NEGATIVE
        elif intensity >= INTENSITY_HIGH:
            return SENTIMENT_NEGATIVE
        else:
            return SENTIMENT_NEUTRAL
    else:
        return SENTIMENT_NEUTRAL




def create_sentiment_entry(task, emotion, sentiment, intensity, category):
    """Build a memory entry."""
    return {
        "timestamp": task["completionDate"],
        "source": "things",
        "task_id": task["id"],
        "title": task["title"],
        "category": category,
        "emotion": emotion,
        "sentiment": sentiment,
        "intensity": intensity,
        "tags": task.get("tags", []),
        "description": task["title"],
    }




def infer_category(task):
    """Derive category string from project or long-delayed completion."""
    # Long-delayed check
    comp_str = task.get("completionDate")
    creation_str = task.get("creationDate")
    if comp_str and creation_str:
        comp = iso_to_datetime(comp_str)
        creation = iso_to_datetime(creation_str)
        if comp is not None and creation is not None:
            if (comp - creation).days >= DELAY_DAYS:
                return CATEGORY_LONG_DELAYED

    proj = (task.get("project") or "").lower()
    if proj in ("inbox", "today"):
        return CATEGORY_INBOX if proj == "inbox" else CATEGORY_TODAY
    if proj == "logbook":
        return CATEGORY_LOGBOOK
    if proj in ("upcoming", "someday"):
        return CATEGORY_UPCOMING
    return CATEGORY_GENERAL




def process_tasks(tasks, memory, state, now=None):
    """Process a batch of tasks, updating memory and state."""
    added = 0
    last_task_id = state.get("last_task_id")
    for task in tasks:
        task_id = task["id"]
        if last_task_id and task_id == last_task_id:
            continue
        emotion, category = map_to_emotion(task)
        intensity = calculate_intensity(task, emotion, now=now)
        sentiment = determine_sentiment(emotion, intensity)
        entry = create_sentiment_entry(task, emotion, sentiment, intensity, category)
        memory["sentiment_entries"].append(entry)
        update_stats(memory["stats"], sentiment)
        last_task_id = task_id
        added += 1
    state["last_task_id"] = last_task_id
    return added


def iso_to_datetime(iso_str):
    """Parse ISO8601 string to datetime, return None if invalid."""
    if not iso_str:
        return None
    try:
        return datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    except Exception:
        return None

def run_poller(args):
    """Main poller orchestration."""
    memory = load_memory(args.output if args.output else MEMORY_FILE)
    state = load_state()
    now = datetime.now(timezone.utc)
    if args.now:
        try:
            now = iso_to_datetime(args.now)
        except Exception:
            print(f"Invalid --now format: {args.now}", file=sys.stderr)
            sys.exit(1)

    if args.verify:
        # Only validate memory, no writes
        valid = validate_memory_schema(memory)
        sys.exit(0 if valid else 1)

    if args.demo:
        tasks = generate_demo_tasks(seed=args.seed, now=now, count=args.demo_count)
        # For demo, isolate state/memory unless output specified
        if args.output:
            memory_path = args.output
            state_path = STATE_FILE.parent / (STATE_FILE.stem + "_demo" + STATE_FILE.suffix)
            memory = load_memory(memory_path)  # load or create fresh
            state = load_state(state_path)
        else:
            memory = {
                "sentiment_entries": [],
                "task_events": [],
                "stats": {k: 0 for k in ["total", "very_positive", "positive", "neutral", "negative", "very_negative"]},
                "created_at": now.isoformat(),
                "last_updated": now.isoformat()
            }
            state = {"last_poll": None, "last_task_id": None}
            state_path = STATE_FILE.parent / (STATE_FILE.stem + "_demo" + STATE_FILE.suffix)
            memory_path = WORKSPACE / "memory_demo.json"
    else:
        tasks = get_completed_tasks(since=state.get("last_poll"))
        state_path = STATE_FILE
        memory_path = args.output or MEMORY_FILE

    added = process_tasks(tasks, memory, state, now=now)
    state["last_poll"] = now.isoformat(timespec='seconds')
    save_state(last_poll=state["last_poll"], last_task_id=state["last_task_id"], path=state_path)
    save_memory(memory, memory_path)

    print(f"Added {added} entries. Total: {memory['stats']['total']}")

    if args.use_demo and args.demo:
        # Copy memory_demo.json to memory.json
        demo_path = args.output or (WORKSPACE / "memory_demo.json")
        import shutil
        shutil.copyfile(demo_path, MEMORY_FILE)
        print(f"Copied {demo_path} → {MEMORY_FILE}")

def validate_memory_schema(memory):
    """Basic schema validation for memory structure."""
    required_keys = ["sentiment_entries", "task_events", "stats", "created_at", "last_updated"]
    for key in required_keys:
        if key not in memory:
            print(f"Missing key: {key}")
            return False
    stats_keys = ["total", "very_positive", "positive", "neutral", "negative", "very_negative"]
    for key in stats_keys:
        if key not in memory["stats"]:
            print(f"Missing stats key: {key}")
            return False
        if not isinstance(memory["stats"][key], int):
            print(f"Stats {key} not int")
            return False
    # Timestamp format check
    try:
        iso_to_datetime(memory["created_at"])  # just validate format
        iso_to_datetime(memory["last_updated"])
    except Exception as e:
        print(f"Timestamp error: {e}")
        return False
    # Sentiment entry fields
    for entry in memory.get("sentiment_entries", []):
        needed = ["timestamp", "source", "task_id", "title", "category", "emotion", "sentiment", "intensity", "tags", "description"]
        for f in needed:
            if f not in entry:
                print(f"Entry missing field {f}")
                return False
        if entry["sentiment"] not in ["very_positive", "positive", "neutral", "negative", "very_negative"]:
            print(f"Invalid sentiment: {entry['sentiment']}")
            return False
        if not (0.0 <= entry["intensity"] <= 1.0):
            print(f"Invalid intensity: {entry['intensity']}")
            return False
        if not isinstance(entry["tags"], list):
            print("tags not list")
            return False
    return True

def main():
    parser = argparse.ArgumentParser(description="Things 3 sentiment poller")
    parser.add_argument("--demo", action="store_true", help="Generate demo tasks")
    parser.add_argument("--demo-count", type=int, default=10, help="Number of demo tasks")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for demo")
    parser.add_argument("--verify", action="store_true", help="Validate memory.json only")
    parser.add_argument("--output", type=str, help="Write to custom file")
    parser.add_argument("--now", type=str, help="Override current time (ISO8601)")
    parser.add_argument("--use-demo", action="store_true", help="After demo, copy memory_demo.json to memory.json")
    args = parser.parse_args()

    run_poller(args)

if __name__ == "__main__":
    main()