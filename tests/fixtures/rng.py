"""Seeded random number generator for reproducible demo task generation."""

import random
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta


class SeededRandom:
    """Deterministic random number generator wrapper."""

    def __init__(self, seed: int):
        self.rng = random.Random(seed)

    def choice(self, seq):
        return self.rng.choice(seq)

    def shuffle(self, seq):
        return self.rng.shuffle(seq)

    def randint(self, a, b):
        return self.rng.randint(a, b)

    def sample(self, population, k):
        return self.rng.sample(population, k)

    def random(self):
        return self.rng.random()


def generate_deterministic_tasks(seed: int, count: int = 10, now: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """
    Generate a deterministic set of tasks for testing/demo purposes.

    Args:
        seed: Random seed for reproducibility
        count: Number of tasks to generate
        now: Reference timestamp (defaults to current time)

    Returns:
        List of task dictionaries with consistent ordering across runs with same seed
    """
    rng = SeededRandom(seed)
    base_time = now or datetime.now(timezone.utc)

    # Task templates categorized by expected emotion
    templates = [
        # Joy (quick wins)
        {"title": "Quick fix: resolved production issue", "project": "Today", "tags": ["quick"], "emotion": "joy"},
        {"title": "Deployed patch without incidents", "project": "Inbox", "tags": ["quick"], "emotion": "joy"},
        {"title": "Code review completed in 5 minutes", "project": "Today", "tags": [], "emotion": "joy"},
        {"title": "Merged PR with no conflicts", "project": "Inbox", "tags": ["quick"], "emotion": "joy"},

        # Motivation (accomplishments)
        {"title": "Launched new feature successfully", "project": "Inbox", "tags": [], "emotion": "motivation"},
        {"title": "Delivered project milestone ahead of schedule", "project": "Today", "tags": [], "emotion": "motivation"},
        {"title": "Completed sprint with 100% completion", "project": "Inbox", "tags": [], "emotion": "motivation"},
        {"title": "Client approved our proposal", "project": "Today", "tags": [], "emotion": "motivation"},

        # Relief (long-delayed)
        {"title": "Finally completed annual tax filing", "project": "Logbook", "tags": [], "emotion": "relief", "delay_days": 90},
        {"title": "Closed legacy ticket from last year", "project": "Logbook", "tags": [], "emotion": "relief", "delay_days": 365},
        {"title": "Finished compliance documentation", "project": "Logbook", "tags": [], "emotion": "relief", "delay_days": 180},

        # Anticipation (future planning)
        {"title": "Planned Q3 roadmap with team", "project": "Upcoming", "tags": [], "emotion": "anticipation"},
        {"title": "Brainstormed new product ideas", "project": "Someday", "tags": [], "emotion": "anticipation"},
        {"title": "Researched upcoming technology trends", "project": "Upcoming", "tags": [], "emotion": "anticipation"},
        {"title": "Created wish list for next release", "project": "Someday", "tags": [], "emotion": "anticipation"},

        # Frustration (overdue/painful)
        {"title": "Overdue client presentation finally done", "project": "Today", "tags": ["overdue"], "emotion": "frustration"},
        {"title": "Resolved production outage", "project": "Inbox", "tags": ["urgent", "overdue"], "emotion": "frustration"},
        {"title": "Fixed broken CI pipeline", "project": "Inbox", "tags": ["urgent"], "emotion": "frustration"},
        {"title": "Reconciled dependency conflicts", "project": "Today", "tags": [], "emotion": "frustration"},

        # Stress (urgent)
        {"title": "Submitted regulatory report at last minute", "project": "Inbox", "tags": ["urgent"], "emotion": "stress"},
        {"title": "Deployed security patch before deadline", "project": "Inbox", "tags": ["urgent"], "emotion": "stress"},
        {"title": "Emergency database migration", "project": "Today", "tags": [], "emotion": "stress"},

        # Neutral (routine)
        {"title": "Weekly maintenance completed", "project": "Logbook", "tags": ["routine"], "emotion": "neutral"},
        {"title": "Updated team documentation", "project": "Inbox", "tags": [], "emotion": "neutral"},
        {"title": "Regular team sync meeting", "project": "Today", "tags": [], "emotion": "neutral"},
    ]

    # Shuffle deterministically
    shuffled = templates[:]
    rng.shuffle(shuffled)

    tasks = []
    for i, template in enumerate(shuffled[:count]):
        delay_days = template.get("delay_days", rng.randint(0, 14))
        creation_offset = timedelta(days=delay_days)

        task = {
            "id": f"demo_seed{seed}_{i+1:03d}",
            "title": template["title"],
            "project": template["project"],
            "tags": template["tags"][:],
            "area": "",
            "completionDate": base_time.isoformat(),
            "creationDate": (base_time - creation_offset).isoformat(),
            # Include metadata for test assertions (not part of real Things schema)
            "_expected_emotion": template["emotion"],
        }
        tasks.append(task)

    return tasks


def validate_demo_task_emotions(tasks: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    Validate that generated demo tasks produce the expected emotions.
    Returns a dict of actual vs expected emotions for debugging.
    """
    from things_sentiment_poller import map_to_emotion

    results = {"matches": [], "mismatches": []}

    for task in tasks:
        actual, _ = map_to_emotion(task)
        expected = task.get("_expected_emotion", "unknown")
        if actual == expected:
            results["matches"].append((task["id"], expected))
        else:
            results["mismatches"].append((task["id"], expected, actual))

    return results
