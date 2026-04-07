"""
Flask web dashboard for OpenClaw Things Sentiment.
Provides cross-platform visualization of sentiment data.
"""

from flask import Flask, render_template, jsonify, send_from_directory
import json
import os
from datetime import datetime

app = Flask(__name__, static_folder='static', template_folder='templates')

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
MEMORY_FILE = os.path.join(DATA_DIR, 'memory.json')


def load_memory():
    """Load sentiment memory from JSON file."""
    try:
        with open(MEMORY_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"entries": [], "last_updated": None}


@app.route('/')
def index():
    """Render main dashboard page."""
    return render_template('index.html')


@app.route('/api/summary')
def api_summary():
    """Return current sentiment summary."""
    memory = load_memory()
    entries = memory.get("entries", [])
    
    if not entries:
        return jsonify({
            "total_entries": 0,
            "average_emotion": None,
            "dominant_category": None,
            "last_updated": None
        })
    
    # Calculate stats
    total = len(entries)
    emotions = [e.get('emotion') for e in entries if e.get('emotion')]
    categories = [e.get('category') for e in entries if e.get('category')]
    
    # Simple dominant calculation
    dominant_emotion = max(set(emotions), key=emotions.count) if emotions else None
    dominant_category = max(set(categories), key=categories.count) if categories else None
    
    # Get latest entry
    latest = entries[-1] if entries else {}
    
    return jsonify({
        "total_entries": total,
        "dominant_emotion": dominant_emotion,
        "dominant_category": dominant_category,
        "latest_entry": latest,
        "last_updated": memory.get("last_updated")
    })


@app.route('/api/entries')
def api_entries():
    """Return all sentiment entries (most recent first)."""
    memory = load_memory()
    entries = memory.get("entries", [])
    # Return reversed for chronological order (newest first)
    return jsonify({"entries": entries[::-1]})


@app.route('/health')
def health():
    """Health check endpoint for monitoring."""
    memory = load_memory()
    last_updated = memory.get("last_updated")
    
    # Simple health check: if we have entries and they're recent (within last 24h)
    healthy = True
    if last_updated:
        try:
            last_dt = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
            age_hours = (datetime.now().astimezone() - last_dt).total_seconds() / 3600
            healthy = age_hours < 24
        except:
            healthy = False
    
    return jsonify({
        "status": "healthy" if healthy else "stale",
        "last_updated": last_updated,
        "service": "things-sentiment-dashboard"
    }), 200 if healthy else 503


if __name__ == '__main__':
    # Ensure data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)
    app.run(host='0.0.0.0', port=8000, debug=True)
