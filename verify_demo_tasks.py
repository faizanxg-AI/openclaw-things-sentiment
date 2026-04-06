#!/usr/bin/env python3
"""Quick validation script for demo task generation."""

from datetime import datetime, timezone, timedelta
from tests.fixtures.demo_tasks import generate_demo_tasks, generate_boundary_task
from tests.fixtures.rng import validate_demo_task_emotions

def main():
    base_time = datetime(2025, 4, 6, 22, 0, 0, tzinfo=timezone.utc)

    print("[*] Generating demo tasks with seed=42...")
    tasks = generate_demo_tasks(seed=42, count=20, base_time=base_time)

    print(f"[+] Generated {len(tasks)} tasks")
    print("\nTask IDs and titles:")
    for t in tasks[:5]:
        print(f"  - {t['id']}: {t['title'][:50]}")

    # Validate emotion expectations
    results = validate_demo_task_emotions(tasks)
    print(f"\n[*] Emotion mapping validation:")
    print(f"    Matches: {len(results['matches'])}")
    print(f"    Mismatches: {len(results['mismatches'])}")

    if results['mismatches']:
        print("\n[!] Mismatched emotions:")
        for tid, expected, actual in results['mismatches'][:5]:
            print(f"  {tid}: expected={expected}, actual={actual}")

    # Generate boundary task
    boundary = generate_boundary_task(base_time, "exact_threshold")
    print(f"\n[*] Boundary task: {boundary['id']}")
    print(f"    Title: {boundary['title']}")
    print(f"    Tags: {boundary['tags']}")

    print("\n[+] Demo task validation complete!")

if __name__ == "__main__":
    main()
