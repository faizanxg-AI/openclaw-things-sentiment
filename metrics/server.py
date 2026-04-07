#!/usr/bin/env python3
"""
HTTP metrics server for Prometheus-compatible endpoint.
Runs in a separate thread within the polling service.
"""

import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional
from .collector import MetricsCollector


class MetricsHandler(BaseHTTPRequestHandler):
    """HTTP handler that serves metrics in Prometheus format."""

    collector: Optional[MetricsCollector] = None

    def do_GET(self):
        """Handle GET requests."""
        if self.path == '/metrics':
            self.send_response(200)
            self.send_header('Content-Type', 'text/plain; version=0.0.4')
            self.end_headers()
            if self.collector:
                metrics = self.collector.export_prometheus()
                self.wfile.write(metrics.encode('utf-8'))
            else:
                self.wfile.write(b"# No collector available\n")
        elif self.path == '/health':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            health = {
                'status': 'healthy',
                'timestamp': time.time(),
                'collector': self.collector is not None
            }
            self.wfile.write(str(health).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        """Suppress request logging."""
        pass


class MetricsServer(threading.Thread):
    """Background HTTP server exposing metrics endpoint."""

    def __init__(self, collector: MetricsCollector, host: str = '0.0.0.0', port: int = 8080):
        super().__init__(daemon=True)
        self.collector = collector
        self.host = host
        self.port = port
        self.server: Optional[HTTPServer] = None
        self.running = False

    def run(self):
        """Start the HTTP server."""
        # Set collector in handler class (shared across all instances)
        MetricsHandler.collector = self.collector

        self.server = HTTPServer((self.host, self.port), MetricsHandler)
        self.running = True
        try:
            self.server.serve_forever()
        except Exception as e:
            print(f"Metrics server error: {e}")
        finally:
            self.running = False

    def stop(self):
        """Stop the server gracefully."""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
        self.running = False

    def is_running(self) -> bool:
        return self.running
