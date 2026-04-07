"""
OpenClaw Automation Rule Engine
Loads and evaluates automation rules for sentiment-based messaging.
"""

import yaml
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class AutomationRule:
    """Represents a single automation rule."""

    def __init__(self, rule_data: Dict[str, Any]):
        self.name = rule_data.get("name", "Unnamed Rule")
        self.emotion = rule_data.get("emotion")
        self.category = rule_data.get("category")
        self.min_intensity = rule_data.get("min_intensity", 0.0)
        self.message_template = rule_data.get("message_template", "")
        self.session_target = rule_data.get("session_target", "main")
        self.enabled = rule_data.get("enabled", True)

        # Cooldown tracking per rule
        self._last_triggered: Optional[datetime] = None

    def matches(self, entry: Dict[str, Any], cooldown_minutes: int = 5) -> bool:
        """Check if a memory entry matches this rule and cooldown has passed."""
        if not self.enabled:
            return False

        # Check cooldown
        if self._last_triggered:
            elapsed = datetime.now(timezone.utc) - self._last_triggered
            if elapsed < timedelta(minutes=cooldown_minutes):
                return False

        # Match emotion
        if self.emotion and entry.get("sentiment") != self.emotion:
            return False

        # Match category (derived from emotion+category or stored category)
        if self.category:
            entry_category = entry.get("category", "")
            if self.category.lower() != entry_category.lower():
                return False

        # Match intensity threshold
        intensity = entry.get("intensity", 0.0)
        if intensity < self.min_intensity:
            return False

        return True

    def format_message(self, entry: Dict[str, Any]) -> str:
        """Format the message template with entry data."""
        context = {
            "title": entry.get("title", ""),
            "description": entry.get("description", ""),
            "sentiment": entry.get("sentiment", ""),
            "intensity": entry.get("intensity", 0.0),
            "timestamp": entry.get("timestamp", ""),
            "category": entry.get("category", ""),
        }
        try:
            return self.message_template.format(**context)
        except KeyError as e:
            logger.warning(f"Template variable missing in rule '{self.name}': {e}")
            return self.message_template

    def trigger(self):
        """Mark this rule as triggered (starts cooldown)."""
        self._last_triggered = datetime.now(timezone.utc)


class RuleEngine:
    """Manages and evaluates automation rules."""

    def __init__(self, config_path: str = "config/automation_rules.yaml"):
        self.config_path = Path(config_path)
        self.rules: List[AutomationRule] = []
        self.settings: Dict[str, Any] = {}
        self.load_config()

    def load_config(self):
        """Load rules and settings from YAML config."""
        if not self.config_path.exists():
            logger.info(f"Automation config not found: {self.config_path}")
            self.settings = {"enabled": False}
            return

        try:
            with open(self.config_path, 'r') as f:
                data = yaml.safe_load(f) or {}

            self.rules = [AutomationRule(rule) for rule in data.get("rules", [])]
            self.settings = data.get("settings", {})
            logger.info(f"Loaded {len(self.rules)} automation rules from {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to load automation config: {e}")
            self.rules = []
            self.settings = {"enabled": False}

    def is_enabled(self) -> bool:
        """Check if automation is globally enabled."""
        return self.settings.get("enabled", False)

    def is_dry_run(self) -> bool:
        """Check if we're in dry-run mode (log only, don't send)."""
        return self.settings.get("dry_run", False)

    def get_cooldown(self) -> int:
        """Get cooldown minutes between triggers."""
        return self.settings.get("cooldown_minutes", 5)

    def get_max_messages(self) -> int:
        """Get maximum messages per run."""
        return self.settings.get("max_messages_per_run", 10)

    def find_matching_rules(self, entry: Dict[str, Any]) -> List[AutomationRule]:
        """Find all enabled rules that match the given entry."""
        matches = []
        for rule in self.rules:
            if rule.matches(entry, self.get_cooldown()):
                matches.append(rule)
        return matches

    def process_entry(self, entry: Dict[str, Any], send_callback) -> List[str]:
        """
        Process a memory entry and send messages for matching rules.

        Args:
            entry: Memory entry dict
            send_callback: Function to call for each matched rule (receives message, session_target)

        Returns:
            List of sent message texts (or logged messages if dry_run)
        """
        if not self.is_enabled():
            return []

        sent_messages = []
        matching_rules = self.find_matching_rules(entry)

        # Limit to max messages per run
        for rule in matching_rules[:self.get_max_messages()]:
            message = rule.format_message(entry)

            if self.is_dry_run():
                logger.info(f"[DRY RUN] Would send to {rule.session_target}: {message}")
                sent_messages.append(f"[DRY RUN] {message}")
            else:
                try:
                    send_callback(message, rule.session_target)
                    rule.trigger()
                    logger.info(f"Sent automation message: {message}")
                    sent_messages.append(message)
                except Exception as e:
                    logger.error(f"Failed to send automation message: {e}")

        return sent_messages
