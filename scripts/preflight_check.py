#!/usr/bin/env python3
"""
Pre-flight checks for OpenClaw Things Sentiment deployment.
Validates environment, dependencies, configuration, and permissions.
Exit code 0 = all clear, non-zero = issues found.
"""

import argparse
import json
import os
import sys
from pathlib import Path
import subprocess
import yaml

class Checker:
    """Run pre-flight validation checks."""

    def __init__(self, verbose=False):
        self.verbose = verbose
        self.issues = []
        self.warnings = []
        self.passed = []

    def info(self, msg):
        if self.verbose:
            print(f"  ℹ️  {msg}")

    def pass_check(self, name, detail=""):
        self.passed.append(name)
        print(f"  ✅ {name}" + (f": {detail}" if detail else ""))

    def fail(self, name, detail="", fix=""):
        self.issues.append((name, detail, fix))
        print(f"  ❌ {name}" + (f": {detail}" if detail else ""))
        if fix:
            print(f"     💡 {fix}")

    def warn(self, name, detail=""):
        self.warnings.append((name, detail))
        print(f"  ⚠️  {name}" + (f": {detail}" if detail else ""))

    def check_python(self):
        """Check Python version."""
        print("\n🔍 Checking Python...")
        try:
            result = subprocess.run(["python3.11", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                self.pass_check("Python 3.11 available", result.stdout.strip())
            else:
                self.fail("Python 3.11 not found", "Required: python3.11", "Install Python 3.11+ from python.org or brew")
        except FileNotFoundError:
            self.fail("Python 3.11 not found", "Required: python3.11", "Install Python 3.11+ from python.org or brew")

    def check_venv(self):
        """Check for virtual environment."""
        print("\n🔍 Checking Virtual Environment...")
        if Path(".venv").exists():
            self.pass_check("Virtual environment exists", ".venv/")
            self.info("Activate with: source .venv/bin/activate")
        else:
            self.warn("No virtual environment", "Recommended for isolation", "Create with: python3.11 -m venv .venv")

    def check_dependencies(self):
        """Check Python dependencies."""
        print("\n🔍 Checking Python Dependencies...")
        req_file = Path("requirements-test.txt")
        if not req_file.exists():
            self.fail("requirements-test.txt missing", "Cannot verify dependencies")
            return

        installed = []
        missing = []
        try:
            result = subprocess.run([sys.executable, "-m", "pip", "list"], capture_output=True, text=True)
            if result.returncode == 0:
                installed = [line.split()[0].lower() for line in result.stdout.split('\n') if line.strip()]
        except:
            pass

        with open(req_file) as f:
            for line in f:
                line = line.strip().split('#')[0].strip()
                if not line:
                    continue
                pkg = line.split('>=')[0].split('==')[0].lower()
                if pkg not in installed:
                    missing.append(pkg)

        if missing:
            self.fail("Missing dependencies", ", ".join(missing), f"Install with: pip install -r {req_file}")
        else:
            self.pass_check("All dependencies installed")

    def check_openclaw(self):
        """Check OpenClaw CLI availability."""
        print("\n🔍 Checking OpenClaw CLI...")
        try:
            result = subprocess.run(["openclaw", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                self.pass_check("OpenClaw CLI available", result.stdout.strip())
                # Try to list sessions
                result = subprocess.run(["openclaw", "sessions", "--json"], capture_output=True, text=True)
                if result.returncode == 0:
                    try:
                        sessions = json.loads(result.stdout)
                        count = len(sessions.get('sessions', []))
                        self.pass_check("OpenClaw sessions accessible", f"{count} session(s) found")
                        if count == 0:
                            self.warn("No active OpenClaw sessions", "Create or join a session first")
                    except:
                        self.warn("Could not parse OpenClaw sessions", "Check your OpenClaw setup")
                else:
                    self.warn("OpenClaw sessions command failed", "Check your OpenClaw setup")
            else:
                self.fail("OpenClaw CLI not working", result.stderr.strip(), "Install OpenClaw: brew install openclaw")
        except FileNotFoundError:
            self.fail("OpenClaw CLI not found", "Required for agent messaging", "Install: brew install openclaw")

    def check_config_files(self):
        """Check configuration files exist and are valid."""
        print("\n🔍 Checking Configuration Files...")
        configs = [
            "config/polling_service.yaml",
            "config/automation_rules.yaml"
        ]
        for cfg in configs:
            path = Path(cfg)
            if not path.exists():
                self.fail(f"Missing config: {cfg}", "Configuration file not found")
                continue
            try:
                with open(path) as f:
                    yaml.safe_load(f)
                self.pass_check(f"Config valid: {cfg}")
            except yaml.YAMLError as e:
                self.fail(f"Invalid YAML: {cfg}", str(e), "Check YAML syntax")

    def check_memory_file(self):
        """Check memory.json exists or can be created."""
        print("\n🔍 Checking Memory File...")
        mem = Path("memory.json")
        if mem.exists():
            try:
                with open(mem) as f:
                    json.load(f)
                self.pass_check("memory.json exists and is valid JSON")
            except json.JSONDecodeError as e:
                self.fail("memory.json is corrupted", str(e), "Run validator: python3 comprehensive_validator.py")
        else:
            self.warn("memory.json not found", "Will be created on first run. Generate demo: make demo")

    def check_permissions(self):
        """Check file permissions for writing."""
        print("\n🔍 Checking File Permissions...")
        # Check if we can write to current directory
        try:
            test_file = Path(".preflight_test")
            test_file.touch()
            test_file.unlink()
            self.pass_check("Write permissions OK", "Can create files in current directory")
        except Exception as e:
            self.fail("No write permissions", str(e), "Check directory permissions")

        # Check script executables
        scripts = ["scripts/start_polling.sh", "scripts/verify_poller.sh"]
        for script in scripts:
            path = Path(script)
            if path.exists() and not os.access(path, os.X_OK):
                self.warn(f"Script not executable: {script}", "Should be executable")
            elif path.exists():
                self.pass_check(f"Script executable: {script}")

    def check_docker(self):
        """Check Docker availability (optional)."""
        print("\n🔍 Checking Docker (optional)...")
        try:
            result = subprocess.run(["docker", "--version"], capture_output=True, text=True)
            if result.returncode == 0:
                self.pass_check("Docker available", result.stdout.strip().split('\n')[0])
            else:
                self.warn("Docker not accessible", result.stderr.strip())
        except FileNotFoundError:
            self.warn("Docker not installed", "Optional for container deployment")
            self.info("To install: Docker Desktop (macOS/Windows) or docker.io (Linux)")

    def check_systemd(self):
        """Check systemd availability (optional)."""
        print("\n🔍 Checking systemd (optional)...")
        if Path("/run/systemd/system").exists() or Path("/etc/systemd/system").exists():
            self.pass_check("systemd available")
            # Check if user systemd is running
            try:
                result = subprocess.run(["systemctl", "--user", "is-running", "systemd"], capture_output=True, text=True)
                if result.returncode == 0:
                    self.pass_check("User systemd active")
                else:
                    self.warn("User systemd not active", "May need to enable: loginctl enable-linger $USER")
            except:
                self.warn("Could not check user systemd")
        else:
            self.warn("systemd not detected", "Optional for service deployment")

    def check_environment(self):
        """Check required environment variables."""
        print("\n🔍 Checking Environment Variables...")
        if os.getenv("OPENCLAW_SESSION_KEY"):
            self.pass_check("OPENCLAW_SESSION_KEY set")
        else:
            self.warn("OPENCLAW_SESSION_KEY not set", "Required for live polling")
            self.info("Export: export OPENCLAW_SESSION_KEY=<your-key>")

    def run_all(self):
        """Run all checks."""
        print("=" * 60)
        print("OpenClaw Things Sentiment - Pre-flight Checks")
        print("=" * 60)

        self.check_python()
        self.check_venv()
        self.check_dependencies()
        self.check_openclaw()
        self.check_config_files()
        self.check_memory_file()
        self.check_permissions()
        self.check_docker()
        self.check_systemd()
        self.check_environment()

        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"  ✅ Passed: {len(self.passed)}")
        print(f"  ⚠️  Warnings: {len(self.warnings)}")
        print(f"  ❌ Failed: {len(self.issues)}")

        if self.issues:
            print("\n🔧 To fix failures:")
            for name, detail, fix in self.issues:
                print(f"  • {name}")
                if fix:
                    print(f"    → {fix}")
            return 1
        else:
            print("\n🎉 All critical checks passed! Ready for deployment.")
            if self.warnings:
                print("   (Warnings present but not blocking)")
            return 0

def main():
    parser = argparse.ArgumentParser(description="Pre-flight validation for OpenClaw Things Sentiment")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show detailed output")
    args = parser.parse_args()

    checker = Checker(verbose=args.verbose)
    sys.exit(checker.run_all())

if __name__ == "__main__":
    main()
