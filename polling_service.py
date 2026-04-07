#!/usr/bin/env python3
"""
Live polling service for Things 3 sentiment tracking.
Runs continuously, polling at configured intervals and sending updates.
"""

import argparse
import json
import os
import signal
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
import logging
import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from automation.rule_engine import RuleEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class PollingService:
    """Continuous polling service with configurable schedule."""

    def __init__(self, config_path="config/polling_service.yaml"):
        self.config_path = Path(config_path)
        self.config = self.load_config()
        self.running = False
        self.rule_engine = RuleEngine()

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.handle_signal)
        signal.signal(signal.SIGTERM, self.handle_signal)

    def load_config(self):
        """Load polling service configuration."""
        default_config = {
            'polling': {
                'interval_minutes': 30,
                'startup_delay_seconds': 5,
                'max_tasks_per_run': 50,
                'use_demo': False  # Set to False for real Things CLI
            },
            'openclaw': {
                'enabled': True,
                'session_key_env': 'OPENCLAW_SESSION_KEY',
                'summary_template': 'Things sentiment update: {total} tasks, latest: {latest_title} ({latest_sentiment})'
            },
            'automation': {
                'enabled': True,
                'config_path': 'config/automation_rules.yaml'
            }
        }

        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    user_config = yaml.safe_load(f) or {}
                # Deep merge (user config overrides defaults)
                self._merge_config(default_config, user_config)
                logger.info(f"Loaded polling config from {self.config_path}")
            except Exception as e:
                logger.error(f"Failed to load config: {e}, using defaults")

        return default_config

    def _merge_config(self, base: dict, update: dict):
        """Recursively merge update into base."""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value

    def handle_signal(self, signum, frame):
        """Handle shutdown signals gracefully."""
        logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

    def poll_once(self):
        """Execute a single polling cycle."""
        logger.info("Starting polling cycle...")

        try:
            # Import here to avoid circular imports
            from things_sentiment_poller import (
                get_completed_tasks, load_memory, save_memory,
                load_state, save_state, process_tasks, iso_to_datetime
            )

            # Load state and memory
            memory = load_memory()
            state = load_state()

            # Determine if using demo or real Things
            use_demo = self.config['polling']['use_demo']
            max_tasks = self.config['polling']['max_tasks_per_run']

            if use_demo:
                # Generate synthetic tasks for demo
                from things_sentiment_poller import generate_demo_tasks
                now = datetime.now(timezone.utc)
                tasks = generate_demo_tasks(seed=int(now.timestamp()) % 1000, now=now, count=min(10, max_tasks))
                logger.info(f"Demo mode: generated {len(tasks)} synthetic tasks")
            else:
                # Real Things CLI polling
                since = state.get("last_poll")
                tasks = get_completed_tasks(since=since, limit=max_tasks)
                logger.info(f"Fetched {len(tasks)} completed tasks from Things")

            if not tasks:
                logger.info("No new tasks to process")
                return True  # Success, nothing to do

            # Process tasks (updates memory and state)
            added = process_tasks(tasks, memory, state)
            logger.info(f"Processed {added} new tasks. Total in memory: {memory['stats']['total']}")

            # Save state and memory
            save_state(last_poll=datetime.now(timezone.utc).isoformat(timespec='seconds'),
                      last_task_id=state.get("last_task_id"))
            save_memory(memory)

            # Send OpenClaw summary if enabled
            if self.config['openclaw']['enabled']:
                self.send_summary(memory)

            # Process automation rules
            if self.config['automation']['enabled']:
                self.process_automation(memory)

            logger.info("Polling cycle completed successfully")
            return True

        except Exception as e:
            logger.error(f"Polling cycle failed: {e}", exc_info=True)
            return False

    def send_summary(self, memory):
        """Send a summary message to OpenClaw."""
        session_key = os.getenv(self.config['openclaw']['session_key_env'])
        if not session_key:
            logger.warning("OPENCLAW_SESSION_KEY not set, skipping summary")
            return

        try:
            latest_entry = memory['sentiment_entries'][-1] if memory['sentiment_entries'] else None
            template = self.config['openclaw']['summary_template']
            latest_title = latest_entry.get('title', 'None') if latest_entry else 'None'
            latest_sentiment = latest_entry.get('sentiment', 'neutral') if latest_entry else 'neutral'

            summary = template.format(
                total=memory['stats']['total'],
                latest_title=latest_title,
                latest_sentiment=latest_sentiment
            )

            import subprocess
            result = subprocess.run(
                ["openclaw", "agent", "--session-id", session_key, "--message", summary, "--json"],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                logger.info(f"Sent OpenClaw summary: {summary}")
            else:
                logger.warning(f"OpenClaw send failed: {result.stderr}")
        except Exception as e:
            logger.error(f"Failed to send OpenClaw summary: {e}")

    def process_automation(self, memory):
        """Process automation rules on latest entries."""
        try:
            # Get recent entries (last 24h maybe?)
            recent = memory['sentiment_entries'][-10:]  # last 10 entries

            def send_callback(message, session_target):
                # Use OpenClaw CLI to send
                session_key = os.getenv(self.config['openclaw']['session_key_env'])
                if not session_key:
                    logger.warning("Cannot send automation: OPENCLAW_SESSION_KEY not set")
                    return

                import subprocess
                result = subprocess.run(
                    ["openclaw", "agent", "--session-id", session_key, "--message", message, "--json"],
                    capture_output=True, text=True, timeout=10
                )
                if result.returncode != 0:
                    raise Exception(f"OpenClaw error: {result.stderr}")

            for entry in recent:
                self.rule_engine.process_entry(entry, send_callback)

        except Exception as e:
            logger.error(f"Automation processing failed: {e}")

    def run(self):
        """Main service loop."""
        logger.info("=" * 60)
        logger.info("OpenClaw Things Sentiment Polling Service Starting")
        logger.info(f"Configuration: {self.config_path}")
        logger.info("=" * 60)

        # Initial delay
        time.sleep(self.config['polling'].get('startup_delay_seconds', 5))

        self.running = True
        interval = self.config['polling']['interval_minutes'] * 60

        while self.running:
            success = self.poll_once()

            if not success:
                logger.warning("Polling cycle failed, will retry after interval")

            # Sleep until next cycle
            logger.info(f"Next poll in {self.config['polling']['interval_minutes']} minutes...")
            for _ in range(int(interval)):
                if not self.running:
                    break
                time.sleep(1)

        logger.info("Polling service stopped gracefully")

def main():
    parser = argparse.ArgumentParser(description="Live polling service for Things sentiment")
    parser.add_argument("--config", type=str, default="config/polling_service.yaml",
                        help="Path to polling service config")
    parser.add_argument("--once", action="store_true",
                        help="Run one poll and exit (for testing)")
    args = parser.parse_args()

    service = PollingService(config_path=args.config)

    if args.once:
        success = service.poll_once()
        sys.exit(0 if success else 1)
    else:
        service.run()

if __name__ == "__main__":
    main()
