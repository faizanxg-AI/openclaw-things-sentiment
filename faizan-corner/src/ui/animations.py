"""Animation patterns for emotion-driven UI feedback."""

import time
import sys
from typing import Callable

# ASCII patterns per emotion
EMOTION_PATTERNS = {
    "joy": [
        "ﾉ･⌣･ﾉ*:･ﾟ✧",
        "♡(⌒‿⌒)♡",
        "⋆݁( ‾́ ∧ ‾́ )݁⋆",
    ],
    "motivation": [
        "🚀 >>>>>>>>",
        "⚡ (ง\'_\')ง",
        "🔥>>>>>===>",
    ],
    "gratitude": [
        "🙏 ✨ ✨",
        "♡⁰⊱ ⠩ ⠆ ⠆ ⠆",
        "✨ ∞ ∞ ∞",
    ],
    "frustration": [
        "(╯°□°)╯",
        "─=≡Σ((( ͠°⌣͡°)",
        "(>‿◠)✌",
    ],
    "fatigue": [
        "(-_-) zzz",
        "(〜￣△￣)〜",
        "(⌒_⌒;)",
    ],
    "calm": [
        "～ ｡ﾟ✧ ～",
        "∘ ∘ ∘",
        "◐ ◐ ◐",
    ],
}

def animate_emotion(emotion: str, duration: float = 2.0, speed: float = 0.3):
    """
    Display a brief ASCII animation for the given emotion.

    Args:
        emotion: Emotion label from EMOTIONS
        duration: Total animation time in seconds
        speed: Delay between frames in seconds
    """
    patterns = EMOTION_PATTERNS.get(emotion, ["( ?_?)"])

    frames = int(duration / speed)
    for i in range(frames):
        pattern = patterns[i % len(patterns)]
        # Clear line and print
        sys.stdout.write("\r" + pattern + "  ")
        sys.stdout.flush()
        time.sleep(speed)
    sys.stdout.write("\r" + " " * 20 + "\r")  # clear
    sys.stdout.flush()

def trigger_ui_reaction(entry) -> Callable:
    """
    Factory that returns a function to trigger UI reaction for a sentiment entry.

    Usage:
      react = trigger_ui_reaction(entry)
      react()  # plays animation, maybe sound later

    Returns a callable that can be invoked in the main loop.
    """
    def _react():
        animate_emotion(entry.emotion, duration=1.5, speed=0.25)
        # Future: integrate with rumps status icon, sound, etc.

    return _react
