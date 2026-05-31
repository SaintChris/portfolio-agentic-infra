#!/usr/bin/env python3
"""Tests for Executive Reporting Agent workflow."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from examples.executive_reporting_agent.workflow import (
    ExecutiveBrief, compute_changes, correlate_events, simulate_crm, simulate_finance,
    simulate_support, simulate_projects, simulate_custom, KNOWN_EVENTS
)

passed = 0
failed = 0

def assert_test(condition, name):
    global passed, failed
    if condition:
        print(f"  PASSED: {name}")
        passed += 1
    else:
        print(f"  FAILED: {name}")
        failed += 1

# Test 1: Data sources return data
crm_data = simulate_crm()
assert_test(isinstance(crm_data, dict), "CRM data is dict")
assert_test("deals" in crm_data or len(crm_data) > 0, "CRM has data")

finance_data = simulate_finance()
assert_test(isinstance(finance_data, dict), "Finance data is dict")

support_data = simulate_support()
assert_test(isinstance(support_data, dict), "Support data is dict")

projects_data = simulate_projects()
assert_test(isinstance(projects_data, dict), "Projects data is dict")

custom_data = simulate_custom()
assert_test(isinstance(custom_data, dict), "Custom data is dict")

# Test 2: change detection works (needs prev + curr)
prev_data = {k: v * 0.9 for k, v in crm_data.items()}  # 10% lower
changes = compute_changes(prev_data, crm_data)
assert_test(isinstance(changes, dict), "Changes computed (dict)")
assert_test(len(changes) > 0, "Changes detected between periods")

# Test 4: ExecutiveBrief dataclass works (agent's version has different fields)
brief = ExecutiveBrief(
    date="2024-01-01",
    headline="Test brief",
    insights=["Test insight"],
    correlated_events=[],
    recommendations=["Test recommendation"],
    metrics_table=""
)
assert_test(brief.date == "2024-01-01", "ExecutiveBrief dataclass works")
assert_test(brief.headline == "Test brief", "ExecutiveBrief headline correct")

# Test 5: Known events are defined
assert_test(len(KNOWN_EVENTS) > 0, "Known events defined")

print(f"\nResults: {passed} passed, {failed} failed")
sys.exit(0 if failed == 0 else 1)
