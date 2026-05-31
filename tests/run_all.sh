#!/usr/bin/env python3
"""
Integration tests for all example agents.
Run: python3 tests/run_all.sh
Individual: python3 tests/test_intake_agent.py
"""

import subprocess
import sys
import os

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)


def run_test(name, test_file):
    """Run a single test file and report result."""
    path = os.path.join(os.path.dirname(__file__), test_file)
    try:
        result = subprocess.run(
            [sys.executable, path],
            capture_output=True, text=True, timeout=30,
            cwd=REPO_ROOT
        )
        if result.returncode == 0:
            # Count PASSED/FAILED from output
            passed = result.stdout.count("PASSED")
            failed = result.stdout.count("FAILED")
            print(f"  ✓ {name}: {passed} passed, {failed} failed")
            return failed == 0
        else:
            print(f"  ✗ {name}: CRASHED (exit {result.returncode})")
            print(f"    {result.stderr[:100]}")
            return False
    except subprocess.TimeoutExpired:
        print(f"  ✗ {name}: TIMEOUT")
        return False
    except Exception as e:
        print(f"  ✗ {name}: ERROR {e}")
        return False


def main():
    print("=" * 60)
    print("  INTEGRATION TEST SUITE — Example Agents")
    print("=" * 60)

    tests = [
        ("Intake Agent", "tests/test_intake_agent.py"),
        ("Finance Ops Agent", "tests/test_finance_ops.py"),
        ("Executive Reporting Agent", "tests/test_executive_reporting.py"),
        ("Field Ops Agent", "tests/test_field_ops.py"),
        ("Knowledge Agent", "tests/test_knowledge_agent.py"),
    ]

    results = []
    for name, test_file in tests:
        results.append(run_test(name, test_file))

    total = len(results)
    passed = sum(results)
    failed = total - passed

    print()
    print(f"Results: {passed}/{total} passed, {failed} failed")
    print("=" * 60)

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
