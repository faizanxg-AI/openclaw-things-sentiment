"""Sentiment analysis engine with per-message and session-level aggregation."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from .emotions import (
    SentimentEntry,
    classify_from_vader,
    detect_source_keywords,
    EMOTIONS,
)

DATA_DIR = Path(__file__).parent.parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
SENTIMENT_LOG = DATA_DIR / "sentiment_log.jsonl"


class SentimentAnalyzer:
    """Analyzes sentiment, maps to emotion labels, and logs entries."""

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = storage_path or SENTIMENT_LOG
        self.storage_path.parent.mkdir(exist_ok=True)

    def analyze_text(
        self,
        text: str,
        source: str = "direct_message",
        vader_score: Optional[float] = None,
        context: Optional[str] = None,
    ) -> SentimentEntry:
        """
        Analyze raw text and produce a sentiment entry.

        Args:
            text: Input text to analyze
            source: Entry source label
            vader_score: Pre-computed VADER compound score (optional)
            context: Additional context (if not provided, uses truncated text)

        Returns:
            SentimentEntry with timestamp, emotion, polarity
        """
        # Check for custom keyword triggers first
        keyword_emotion, keyword_polarity = detect_source_keywords(text)
        if keyword_emotion:
            polarity = keyword_polarity
            emotion = keyword_emotion
        else:
            # Use VADER if provided, otherwise neutral
            if vader_score is None:
                vader_score = 0.0  # Placeholder - integrate real VADER later
            emotion = classify_from_vader(vader_score)
            polarity = vader_score

        entry = SentimentEntry(
            timestamp=datetime.utcnow().isoformat() + "Z",
            source=source,
            polarity=round(polarity, 3),
            emotion=emotion,
            context=context or text[:100],
        )
        self._log_entry(entry)
        return entry

    def log_things_completion(
        self, count: int, project: str = "General"
    ) -> SentimentEntry:
        """Create a sentiment entry from Things completion event."""
        context = f"Completed {count} tasks in '{project}'"
        # Things completion is strongly positive motivation
        entry = SentimentEntry(
            timestamp=datetime.utcnow().isoformat() + "Z",
            source="things_completion",
            polarity=0.8,
            emotion="motivation",
            context=context,
        )
        self._log_entry(entry)
        return entry

    def _log_entry(self, entry: SentimentEntry) -> None:
        """Append entry to storage file."""
        with open(self.storage_path, "a") as f:
            f.write(json.dumps(entry.to_json()) + "\n")

    def get_recent(self, limit: int = 100) -> List[SentimentEntry]:
        """Load recent entries for session-level aggregation."""
        entries = []
        if not self.storage_path.exists():
            return entries
        with open(self.storage_path, "r") as f:
            lines = f.readlines()[-limit:]
            for line in lines:
                data = json.loads(line.strip())
                entries.append(SentimentEntry(**data))
        return entries

    def aggregate_by_timewindow(
        self, entries: List[SentimentEntry], window_minutes: int = 30
    ) -> Dict[str, Dict[str, int]]:
        """
        Aggregate emotion counts over time windows.

        Returns: {"2024-01-01T12:00": {"joy": 3, "motivation": 1, ...}, ...}
        """
        from collections import defaultdict
        windows = defaultdict(lambda: defaultdict(int))

        for entry in entries:
            # Simple bucketing by minute for now
            ts = datetime.fromisoformat(entry.timestamp.replace("Z", ""))
            bucket = ts.replace(second=0, microsecond=0).isoformat() + "Z"
            windows[bucket][entry.emotion] += 1

        return dict(windows)

    def get_current_mood_profile(self, entries: List[SentimentEntry]) -> str:
        """
        Generate a natural language mood summary from recent entries.
        Example: "Faizan's having a focused morning" or "needs a boost"
        """
        if not entries:
            return "Mood data gathering..."

        emotion_counts = {}
        for e in entries[-20:]:  # last 20 entries
            emotion_counts[e.emotion] = emotion_counts.get(e.emotion, 0) + 1

        top_emotion = max(emotion_counts, key=emotion_counts.get)

        mood_phrases = {
            "joy": "Feeling positive and energized!",
            "motivation": "In a productive, motivated state",
            "gratitude": "Reflecting with appreciation",
            "calm": "Calm and steady focus",
            "frustration": "Encountering some friction",
            "fatigue": "Running low on energy",
        }
        return mood_phrases.get(top_emotion, "Mixed emotional state")
