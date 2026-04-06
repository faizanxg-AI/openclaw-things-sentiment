#!/usr/bin/env python3
"""
Hermes Rumps UI Layer
Menu bar app with sentiment visualization, appreciation display, and dashboard.
"""

import os
import json
import time
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

import rumps
import pync

# Configuration
WORKSPACE = Path.home() / "agent-bridge" / "workspace"
MEMORY_FILE = WORKSPACE / "memory.json"
ICON_SIZE = 16

# Sentiment intensity mapping for colors
SENTIMENT_COLORS = {
    "very_positive": "#00FF00",  # Green
    "positive": "#7FFF00",       # Light Green
    "neutral": "#FFD700",        # Gold
    "negative": "#FF8C00",       # Orange
    "very_negative": "#FF0000",  # Red
}

class MemoryManager:
    """Handle persistence of sentiment entries and task events."""
    
    def __init__(self, memory_path):
        self.memory_path = Path(memory_path)
        self.data = self.load()
    
    def load(self):
        if self.memory_path.exists():
            with open(self.memory_path, 'r') as f:
                return json.load(f)
        return {"sentiment_entries": [], "task_events": [], "stats": {}}
    
    def save(self):
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.memory_path, 'w') as f:
            json.dump(self.data, f, indent=2)
    
    def add_sentiment(self, text, sentiment, intensity, source="openclaw"):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "text": text,
            "sentiment": sentiment,
            "intensity": intensity,
            "source": source
        }
        self.data["sentiment_entries"].append(entry)
        self._update_stats(sentiment)
        self.save()
        return entry
    
    def add_task_event(self, task_id, status, source="things"):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "task_id": task_id,
            "status": status,
            "source": source
        }
        self.data["task_events"].append(entry)
        self.save()
        return entry
    
    def _update_stats(self, sentiment):
        stats = self.data.get("stats", {})
        stats[sentiment] = stats.get(sentiment, 0) + 1
        stats["total"] = sum(stats.get(k, 0) for k in SENTIMENT_COLORS.keys())
        self.data["stats"] = stats
    
    def get_latest_appreciation(self):
        entries = self.data.get("sentiment_entries", [])
        # Filter to last 14 days only
        cutoff = datetime.now(timezone.utc) - timedelta(days=14)
        recent = [e for e in entries if datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00")) >= cutoff]
        if not recent:
            return "No recent appreciation"
        latest = recent[-1]
        # Use title if available, fallback to description or truncate title
        display_text = latest.get('title') or latest.get('description', 'Appreciation')
        if len(display_text) > 60:
            display_text = display_text[:57] + '...'
        return f"{display_text} ({latest['sentiment']})"
    
    def get_stats(self):
        cutoff = datetime.now(timezone.utc) - timedelta(days=14)
        entries = self.data.get("sentiment_entries", [])
        recent = [e for e in entries if datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00")) >= cutoff]
        # Recompute stats from recent entries only
        stats = {k: 0 for k in SENTIMENT_COLORS.keys()}
        for entry in recent:
            sentiment = entry.get("sentiment")
            if sentiment in stats:
                stats[sentiment] += 1
        total = len(recent)
        return stats, total

class OpenClawBridge:
    """Bridge to OpenClaw CLI for real-time data."""
    
    @staticmethod
    def get_sessions():
        try:
            result = subprocess.run(
                ["openclaw", "sessions", "--json"],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                return data.get("sessions", [])
        except Exception as e:
            print(f"OpenClaw error: {e}")
        return []
    
    @staticmethod
    def send_message(session_key, text):
        """Send a message to an OpenClaw session using the agent command."""
        try:
            result = subprocess.run(
                ["openclaw", "agent", "--session-id", session_key, "--message", text, "--json"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return True
            else:
                print(f"OpenClaw send error: {result.stderr}")
                return False
        except Exception as e:
            print(f"Send error: {e}")
            return False

class HermesMenuBarApp(rumps.App):
    """Main menu bar application."""
    
    def __init__(self):
        super().__init__("Hermes", icon=None, quit_button=None)
        self.memory = MemoryManager(MEMORY_FILE)
        self.openclaw = OpenClawBridge()
        self.current_session = None
        self._last_sessions = []
        
        # Refresh sessions immediately
        self.refresh_sessions()
        
        # Start periodic session refresh (every 60s)
        self.refresh_timer = rumps.Timer(self.refresh_sessions, 60.0)
        self.refresh_timer.start()
        
        # Icon state
        self.current_color = SENTIMENT_COLORS["neutral"]
        self.pulse_state = False
        
        # Setup menu
        self.menu = [
            "Show Dashboard",
            "Latest Appreciation:",
            self._make_appreciation_item(),
            None,  # Separator
            "Sentiment Stats:",
            self._make_stats_item(),
            None,
            "OpenClaw Sessions:",
            self._make_sessions_item(),
            None,
            "Send Message:",
            "Test Notification",
            "Quit"
        ]
        
        # Start icon animation
        rumps.Timer(self._update_icon, 1.0).start()
    
    def refresh_sessions(self, _=None):
        """Fetch latest sessions and select the most recent active one."""
        sessions = self.openclaw.get_sessions()
        self._last_sessions = sessions
        if sessions:
            # Pick the most recently updated session (updatedAt is in ms since epoch)
            sessions_sorted = sorted(sessions, key=lambda s: s.get("updatedAt", 0), reverse=True)
            self.current_session = sessions_sorted[0]["key"]
        else:
            self.current_session = None
        # Update menu items that show sessions count
        self._update_sessions_item()
    
    def _make_appreciation_item(self):
        return rumps.MenuItem(self.memory.get_latest_appreciation())
    
    def _make_stats_item(self):
        stats, total = self.memory.get_stats()
        lines = [f"{k}: {stats.get(k, 0)}" for k in SENTIMENT_COLORS.keys()]
        lines.append(f"Total: {total}")
        return rumps.MenuItem("\n".join(lines))
    
    def _make_sessions_item(self):
        count = len(self._last_sessions)
        if count == 0:
            return rumps.MenuItem("No sessions")
        return rumps.MenuItem(f"{count} active")
    
    def _update_sessions_item(self):
        # Find and update the sessions menu item
        for idx, item in enumerate(self.menu):
            if isinstance(item, rumps.MenuItem) and "OpenClaw Sessions:" in (item.title or ""):
                if idx + 1 < len(self.menu):
                    sessions_item = self.menu[idx + 1]
                    sessions_item.title = self._make_sessions_item().title
                break
    
    @rumps.clicked("Show Dashboard")
    def show_dashboard(self, _):
        """Open dashboard window."""
        DashboardWindow(self).show()
    
    @rumps.clicked("Test Notification")
    def test_notification(self, _):
        """Test notification."""
        # Create a local sentiment entry
        self.memory.add_sentiment("Test notification from Hermes UI", "positive", "medium")
        self._refresh_menu()
        # Also send to OpenClaw if we have a session
        if self.current_session:
            success = self.openclaw.send_message(self.current_session, "Test notification from Hermes UI")
            if success:
                print("Sent test notification to OpenClaw session:", self.current_session)
            else:
                print("Failed to send test notification to OpenClaw")
        else:
            print("No OpenClaw session selected; not sending")
        # Show a notification
        rumps.notification("Hermes", None, "Test notification sent")
    
    @rumps.clicked("Quit")
    def quit(self, _):
        self.refresh_timer.stop()
        rumps.quit_application()
    
    def _update_icon(self, _):
        """Animate icon based on sentiment intensity."""
        # Simple pulse effect by swapping colors
        self.pulse_state = not self.pulse_state
        
        # Determine current color from latest sentiment
        latest = self.memory.get_latest_appreciation()
        # For now use neutral pulse; wire to real sentiment later
        color = SENTIMENT_COLORS["neutral"]
        
        self.icon = self._create_colored_icon(color)
    
    def _create_colored_icon(self, color_hex):
        """Create a simple colored icon (Placeholder)."""
        # In a real implementation, we'd generate a proper icon
        # For now return None (use system default)
        return None
    
    def _refresh_menu(self):
        """Update menu items with latest data."""
        # Update appreciation item
        appreciation_item = self.menu["Latest Appreciation:"].submenu[1]
        appreciation_item.title = self.memory.get_latest_appreciation()
        
        # Update stats item
        stats_item = self.menu["Sentiment Stats:"].submenu[1]
        stats, total = self.memory.get_stats()
        lines = [f"{k}: {stats.get(k, 0)}" for k in SENTIMENT_COLORS.keys()]
        lines.append(f"Total: {total}")
        stats_item.title = "\n".join(lines)
        
        # Update sessions count
        self._update_sessions_item()

class DashboardWindow(rumps.Window):
    """Dashboard window showing aggregated stats."""
    
    def __init__(self, app):
        super().__init__(
            title="Hermes Dashboard",
            message=self._generate_dashboard(app),
            ok="Close",
            cancel=None,
            dimensions=(400, 300)
        )
        self.app = app
    
    def _generate_dashboard(self, app):
        stats, total = app.memory.get_stats()
        
        dashboard = [
            "=== Hermes Dashboard ===",
            f"Total Events (14d): {total}",
            "\nSentiment Breakdown:",
        ]
        
        for sentiment, count in stats.items():
            bar = "█" * min(count, 20)
            dashboard.append(f"  {sentiment:15} {count:4} {bar}")
        
        # Recent appreciation messages (last 14 days, last 5)
        entries = app.memory.data["sentiment_entries"]
        cutoff = datetime.now(timezone.utc) - timedelta(days=14)
        recent = [e for e in entries if datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00")) >= cutoff]
        recent = recent[-5:]
        dashboard.append("\n=== Latest Appreciation ===")
        for entry in reversed(recent):
            time_str = datetime.fromisoformat(entry["timestamp"]).strftime("%H:%M")
            # Use title if available, fallback to description
            display_text = entry.get('title') or entry.get('description', 'Appreciation')
            dashboard.append(f"  [{time_str}] {display_text}")
        
        # OpenClaw status
        sessions = app._last_sessions
        dashboard.append(f"\nOpenClaw Sessions: {len(sessions)}")
        
        return "\n".join(dashboard)

def main():
    """Entry point."""
    # Ensure workspace exists
    WORKSPACE.mkdir(parents=True, exist_ok=True)
    
    # Start the app
    HermesMenuBarApp().run()

if __name__ == "__main__":
    main()
