"""Core orchestration: window, menu bar, state, integration glue."""

from pathlib import Path
from typing import Callable
from ..sentiment.analyzer import SentimentAnalyzer
from ..ui.animations import trigger_ui_reaction


class AppController:
    def __init__(self):
        self.state = {
            "launched": True,
            "tasks_completed": 0,
            "messages_sent": 0,
        }
        self.analyzer = SentimentAnalyzer()
        self._reaction_handlers = []

    def run(self):
        print("Faizan's Corner is running with Sentiment Analyzer")
        # In real app, this starts rumps/UI loop
        # For now, expose hooks for integration

    # --- Integration hooks ---

    def on_things_completion(self, count: int, project: str = "General"):
        """Called when Things tasks are completed (via webhook or CLI bridge)."""
        entry = self.analyzer.log_things_completion(count, project)
        self.state["tasks_completed"] += count
        self._trigger_reaction(entry)
        print(f"✓ Things completion logged: {entry.context} → {entry.emotion}")
        return entry

    def on_message_sent(self, text: str, vader_score: float = None):
        """Called when a message is sent (by user or observed)."""
        entry = self.analyzer.analyze_text(
            text=text,
            source="direct_message",
            vader_score=vader_score,
            context=f"User said: {text[:80]}"
        )
        self.state["messages_sent"] += 1
        self._trigger_reaction(entry)
        print(f"💬 Message analyzed: {entry.emotion} (polarity {entry.polarity})")
        return entry

    def on_observation(self, text: str, source: str = "observation"):
        """Called for passive observations (e.g., system logs, user activity)."""
        entry = self.analyzer.analyze_text(text=text, source=source)
        self._trigger_reaction(entry)
        return entry

    def get_mood_profile(self) -> str:
        """Return natural language mood summary for UI display."""
        recent = self.analyzer.get_recent(limit=50)
        return self.analyzer.get_current_mood_profile(recent)

    def get_session_stats(self) -> dict:
        """Aggregate stats for the current session window (e.g., last 30min)."""
        recent = self.analyzer.get_recent(limit=100)
        return {
            "total_entries": len(recent),
            "emotion_distribution": self._distribution(recent),
            "mood_profile": self.get_mood_profile(),
        }

    def _distribution(self, entries):
        from collections import Counter
        return dict(Counter(e.emotion for e in entries))

    # --- Reaction system ---

    def _trigger_reaction(self, entry):
        """Invoke all registered UI reaction callbacks."""
        for handler in self._reaction_handlers:
            try:
                handler(entry)
            except Exception as e:
                print(f"Reaction error: {e}")

    def on_reaction(self, callback: Callable):
        """Register a callback to receive sentiment entries for UI feedback."""
        self._reaction_handlers.append(callback)


# Quick demo
if __name__ == "__main__":
    app = AppController()
    app.on_reaction(trigger_ui_reaction)

    print("Initial mood:", app.get_mood_profile())
    # Demo events
    app.on_things_completion(3, "Project X")
    app.on_message_sent("Just finished my morning review!", vader_score=0.72)
    app.on_message_sent("Ugh, this bug is impossible", vader_score=-0.52)
    print("\nSession stats:", app.get_session_stats())
