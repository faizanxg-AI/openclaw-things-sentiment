#!/usr/bin/env python3
"""
Metrics collector for Things sentiment poller.
Tracks operational metrics for monitoring and alerting.
"""

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Optional, Dict, List
from datetime import datetime, timezone


@dataclass
class PollMetrics:
    """Metrics for a single poll cycle."""
    duration: float  # seconds
    success: bool
    tasks_processed: int
    sentiment_added: int
    openclaw_sent: bool
    automation_triggered: int
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class MetricsCollector:
    """Collects and aggregates metrics for the polling service."""

    def __init__(self, max_history: int = 100):
        self.max_history = max_history
        self.poll_history: deque = deque(maxlen=max_history)

        # Gauges (current values)
        self._total_polls = 0
        self._total_successes = 0
        self._total_failures = 0
        self._total_tasks_processed = 0
        self._total_sentiment_added = 0
        self._total_automation_triggers = 0
        self._openclaw_connected = 0
        self._last_poll_time: Optional[datetime] = None

        # Alert state
        self._alerts_active: Dict[str, bool] = {}

        # Rolling window for rates (last 10 polls)
        self._recent_polls: deque = deque(maxlen=10)

    def start_poll(self) -> float:
        """Mark start of a poll cycle, return start timestamp."""
        return time.time()

    def record_poll_complete(self, start_time: float, **kwargs):
        """Record completion of a poll cycle."""
        duration = time.time() - start_time
        metrics = PollMetrics(
            duration=duration,
            success=kwargs.get('success', True),
            tasks_processed=kwargs.get('tasks_processed', 0),
            sentiment_added=kwargs.get('sentiment_added', 0),
            openclaw_sent=kwargs.get('openclaw_sent', False),
            automation_triggered=kwargs.get('automation_triggered', 0)
        )
        self.poll_history.append(metrics)

        # Update totals
        self._total_polls += 1
        if metrics.success:
            self._total_successes += 1
        else:
            self._total_failures += 1
        self._total_tasks_processed += metrics.tasks_processed
        self._total_sentiment_added += metrics.sentiment_added
        self._total_automation_triggers += metrics.automation_triggered
        self._last_poll_time = metrics.timestamp

        # Update recent polls for rate calculations
        self._recent_polls.append(metrics.success)

    def set_openclaw_status(self, connected: bool):
        """Update OpenClaw connection status."""
        self._openclaw_connected = 1 if connected else 0

    def increment_automation_triggers(self, count: int = 1):
        """Increment automation trigger count (for rules triggered outside poll)."""
        self._total_automation_triggers += count

    # --- Getters for current state ---

    @property
    def total_polls(self) -> int:
        return self._total_polls

    @property
    def success_rate_recent(self) -> float:
        """Success rate over last 10 polls (0.0-1.0)."""
        if not self._recent_polls:
            return 1.0
        return sum(self._recent_polls) / len(self._recent_polls)

    @property
    def average_poll_duration(self) -> float:
        """Average poll duration over history."""
        if not self.poll_history:
            return 0.0
        return sum(m.duration for m in self.poll_history) / len(self.poll_history)

    @property
    def last_poll_duration(self) -> Optional[float]:
        """Duration of most recent poll."""
        if self.poll_history:
            return self.poll_history[-1].duration
        return None

    @property
    def openclaw_connected(self) -> int:
        return self._openclaw_connected

    @property
    def total_tasks_processed(self) -> int:
        return self._total_tasks_processed

    @property
    def total_sentiment_added(self) -> int:
        return self._total_sentiment_added

    @property
    def uptime_seconds(self) -> float:
        """Approximate uptime based on first poll."""
        if self.poll_history:
            first = self.poll_history[0].timestamp
            last = self.poll_history[-1].timestamp
            return (last - first).total_seconds()
        return 0.0

    # --- Prometheus text format export ---

    def export_prometheus(self) -> str:
        """Export metrics in Prometheus text exposition format."""
        lines = []
        lines.append("# HELP polls_total Total number of polls executed")
        lines.append("# TYPE polls_total counter")
        lines.append(f"polls_total {self._total_polls}")

        lines.append("# HELP polls_successful Total number of successful polls")
        lines.append("# TYPE polls_successful counter")
        lines.append(f"polls_successful {self._total_successes}")

        lines.append("# HELP polls_failed Total number of failed polls")
        lines.append("# TYPE polls_failed counter")
        lines.append(f"polls_failed {self._total_failures}")

        lines.append("# HELP poll_duration_seconds Poll duration histogram (current)")
        lines.append("# TYPE poll_duration_seconds gauge")
        last_dur = self.last_poll_duration or 0
        lines.append(f"poll_duration_seconds {last_dur:.3f}")

        lines.append("# HELP poll_duration_average_seconds Average poll duration")
        lines.append("# TYPE poll_duration_average_seconds gauge")
        lines.append(f"poll_duration_average_seconds {self.average_poll_duration:.3f}")

        lines.append("# HELP success_rate_recent Recent success rate (last 10 polls)")
        lines.append("# TYPE success_rate_recent gauge")
        lines.append(f"success_rate_recent {self.success_rate_recent:.3f}")

        lines.append("# HELP tasks_processed_total Total tasks processed")
        lines.append("# TYPE tasks_processed_total counter")
        lines.append(f"tasks_processed_total {self._total_tasks_processed}")

        lines.append("# HELP sentiment_entries_total Total sentiment entries added")
        lines.append("# TYPE sentiment_entries_total counter")
        lines.append(f"sentiment_entries_total {self._total_sentiment_added}")

        lines.append("# HELP automation_triggers_total Total automation triggers")
        lines.append("# TYPE automation_triggers_total counter")
        lines.append(f"automation_triggers_total {self._total_automation_triggers}")

        lines.append("# HELP openclaw_connected OpenClaw connection status (1=connected)")
        lines.append("# TYPE openclaw_connected gauge")
        lines.append(f"openclaw_connected {self._openclaw_connected}")

        lines.append("# HELP service_uptime_seconds Approximate service uptime")
        lines.append("# TYPE service_uptime_seconds gauge")
        lines.append(f"service_uptime_seconds {self.uptime_seconds:.0f}")

        return "\n".join(lines)

    def get_state_snapshot(self) -> dict:
        """Get a snapshot of current metrics as a dictionary."""
        return {
            'total_polls': self._total_polls,
            'total_successes': self._total_successes,
            'total_failures': self._total_failures,
            'success_rate_recent': self.success_rate_recent,
            'average_poll_duration': self.average_poll_duration,
            'last_poll_duration': self.last_poll_duration,
            'total_tasks_processed': self._total_tasks_processed,
            'total_sentiment_added': self._total_sentiment_added,
            'total_automation_triggers': self._total_automation_triggers,
            'openclaw_connected': bool(self._openclaw_connected),
            'last_poll_time': self._last_poll_time.isoformat() if self._last_poll_time else None,
            'uptime_seconds': self.uptime_seconds
        }
