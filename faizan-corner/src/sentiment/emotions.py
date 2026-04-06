"""Emotion classification and VADER mapping."""

from dataclasses import dataclass
from typing import Dict, List

# Emotion labels as specified
EMOTIONS = ["joy", "motivation", "gratitude", "frustration", "fatigue", "calm"]

# VADER compound score thresholds → emotion mapping
# Based on: https://github.com/cjhutto/vaderSentiment
VADER_TO_EMOTION = {
    "joy": lambda c: c >= 0.6,
    "motivation": lambda c: 0.4 <= c < 0.6,  # Positive, but not full joy
    "calm": lambda c: 0.2 <= c < 0.4,
    "frustration": lambda c: -0.4 <= c < -0.1,
    "fatigue": lambda c: -0.6 <= c < -0.4,
    # Default fallback for extreme ranges
}

# Custom keyword triggers for Things completion and other sources
KEYWORD_EMOTION_MAP = {
    "completed": "motivation",
    "finished": "motivation",
    "done": "motivation",
    "accomplished": "motivation",
    "achieved": "motivation",
    "thank": "gratitude",
    "thanks": "gratitude",
    "grateful": "gratitude",
    "exhausted": "fatigue",
    "tired": "fatigue",
    "overwhelmed": "frustration",
    "stuck": "frustration",
}


@dataclass
class SentimentEntry:
    """Standardized sentiment record for memory storage."""
    timestamp: str
    source: str  # "things_completion" | "direct_message" | "observation"
    polarity: float  # -1.0 to 1.0
    emotion: str  # one of EMOTIONS
    context: str  # human-readable description

    def to_json(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "source": self.source,
            "polarity": self.polarity,
            "emotion": self.emotion,
            "context": self.context,
        }


def classify_from_vader(compound_score: float) -> str:
    """Map VADER compound score to emotion label."""
    for emotion, condition in VADER_TO_EMOTION.items():
        if condition(compound_score):
            return emotion
    # Neutral/low intensity → calm
    return "calm"


def detect_source_keywords(text: str) -> tuple[str | None, float]:
    """Check for custom keyword triggers. Returns (emotion, polarity) or (None, 0)."""
    text_lower = text.lower()
    for keyword, emotion in KEYWORD_EMOTION_MAP.items():
        if keyword in text_lower:
            # Approximate polarity based on emotion
            polarity_map = {
                "motivation": 0.7,
                "gratitude": 0.8,
                "frustration": -0.5,
                "fatigue": -0.6,
            }
            return emotion, polarity_map.get(emotion, 0.0)
    return None, 0.0
