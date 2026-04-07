#!/usr/bin/env python3
"""
Alert manager that monitors metrics and sends OpenClaw notifications
when configured thresholds are breached.
"""

import os
import time
import logging
from dataclasses import dataclass
from typing import Dict, List, Optional
from datetime import datetime, timezone, timedelta
import subprocess

logger = logging.getLogger(__name__)


@dataclass
class AlertRule:
    """Definition of an alert threshold and notification."""
    name: str
    condition: str  # e.g., "success_rate_recent < 0.8"
    severity: str  # "warning" or "critical"
    message: str  # Alert message template with {metrics} format
    cooldown_minutes: int = 15  # Minimum time between repeat alerts

    # Internal state
    _last_triggered: Optional[datetime] = None
    _currently_active: bool = False

    def check(self, metrics_dict: dict) -> bool:
        """Evaluate condition against metrics dict."""
        try:
            # Simple evaluation: create local context with metrics
            context = metrics_dict.copy()
            # Add time helpers if needed
            return eval(self.condition, {"__builtins__": {}}, context)
        except Exception as e:
            logger.error(f"Alert rule '{self.name}' evaluation failed: {e}")
            return False

    def is_cooldown_expired(self) -> bool:
        """Check if enough time has passed since last alert."""
        if self._last_triggered is None:
            return True
        elapsed = datetime.now(timezone.utc) - self._last_triggered
        return elapsed > timedelta(minutes=self.cooldown_minutes)

    def should_alert(self, metrics_dict: dict) -> bool:
        """Determine if alert should fire now."""
        condition_met = self.check(metrics_dict)
        cooldown_ok = self.is_cooldown_expired()

        # If condition is met and cooldown expired, alert
        if condition_met and cooldown_ok:
            return True
        return False

    def trigger(self):
        """Mark alert as triggered now."""
        self._last_triggered = datetime.now(timezone.utc)
        self._currently_active = True

    def resolve(self):
        """Mark alert as resolved."""
        self._currently_active = False


class AlertManager:
    """Monitors metrics and sends alerts via OpenClaw."""

    DEFAULT_RULES = [
        AlertRule(
            name="high_failure_rate",
            condition="success_rate_recent < 0.8",
            severity="warning",
            message="High poll failure rate detected: {success_rate_recent:.1%} (threshold: 80%). Last {total_polls} polls: {total_failures} failed.",
            cooldown_minutes=15
        ),
        AlertRule(
            name="slow_poll",
            condition="last_poll_duration > 300",  # > 5 minutes
            severity="warning",
            message="Slow poll detected: {last_poll_duration:.0f}s (threshold: 300s). Average: {average_poll_duration:.0f}s.",
            cooldown_minutes=10
        ),
        AlertRule(
            name="no_openclaw",
            condition="openclaw_connected == 0",
            severity="critical",
            message="OpenClaw connection lost. Notifications disabled. Check OPENCLAW_SESSION_KEY and network.",
            cooldown_minutes=30
        ),
        AlertRule(
            name="stale_service",
            condition="(datetime.now(timezone.utc) - datetime.fromisoformat(last_poll_time.replace('Z', '+00:00'))).total_seconds() > 900" if None else False,
            # This rule is evaluated differently due to timestamp parsing
            severity="critical",
            message="Service appears stalled: no polls in last 15 minutes. Last poll: {last_poll_time}",
            cooldown_minutes=60
        ),
    ]

    def __init__(self, collector, openclaw_session_key: Optional[str] = None,
                 rules: Optional[List[AlertRule]] = None):
        self.collector = collector
        self.session_key = openclaw_session_key or os.getenv('OPENCLAW_SESSION_KEY')
        self.rules = rules or self.DEFAULT_RULES
        self._alert_states: Dict[str, bool] = {}  # Track active alerts

    def check_and_alert(self) -> List[str]:
        """
        Evaluate all rules and send alerts for breached thresholds.
        Returns list of alert messages sent.
        """
        metrics = self.collector.get_state_snapshot()
        alerts_sent = []

        for rule in self.rules:
            # Special handling for stale service rule (needs timestamp parsing)
            if rule.name == "stale_service":
                try:
                    last = metrics.get('last_poll_time')
                    if last:
                        last_dt = datetime.fromisoformat(last.replace('Z', '+00:00'))
                        stale_seconds = (datetime.now(timezone.utc) - last_dt).total_seconds()
                        condition_met = stale_seconds > 900
                    else:
                        condition_met = True  # never polled
                except Exception:
                    condition_met = False
            else:
                condition_met = rule.check(metrics)

            if condition_met and rule.should_alert(metrics):
                # Build alert message
                msg = rule.message.format(**metrics)
                full_msg = f"[{rule.severity.upper()}] {rule.name}: {msg}"

                # Send via OpenClaw if available
                if self.session_key:
                    sent = self._send_openclaw_message(full_msg)
                    if sent:
                        rule.trigger()
                        alerts_sent.append(full_msg)
                        logger.warning(f"Alert sent: {rule.name}")
                    else:
                        logger.error(f"Failed to send alert: {rule.name}")
                else:
                    logger.warning(f"Alert condition {rule.name} but no OpenClaw session key")
                    # Still trigger to avoid spamming
                    rule.trigger()

            elif not condition_met and rule._currently_active:
                # Condition resolved
                rule.resolve()
                logger.info(f"Alert resolved: {rule.name}")

        return alerts_sent

    def _send_openclaw_message(self, message: str) -> bool:
        """Send a message through OpenClaw agent."""
        try:
            result = subprocess.run(
                ["openclaw", "agent", "--session-id", self.session_key,
                 "--message", message, "--json"],
                capture_output=True, text=True, timeout=10
            )
            return result.returncode == 0
        except Exception as e:
            logger.error(f"OpenClaw send failed: {e}")
            return False

    def get_active_alerts(self) -> List[dict]:
        """Get list of currently active (unresolved) alerts."""
        return [
            {'name': rule.name, 'severity': rule.severity, 'last_triggered': rule._last_triggered}
            for rule in self.rules if rule._currently_active
        ]
