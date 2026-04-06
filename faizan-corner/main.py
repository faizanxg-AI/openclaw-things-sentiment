#!/usr/bin/env python3
"""
Faizan's Corner — Appreciation Dashboard
Main entry point.
"""

from src.core.app import AppController

def main():
    app = AppController()
    app.run()

if __name__ == "__main__":
    main()