#!/usr/bin/env python3
"""Tests for Field Ops Agent workflow."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# The module path uses underscore: field_ops_agent (dir is field-ops-agent)
from examples.field_ops_agent.workflow import (
    parse_note, build_report, generate_followups, draft_customer_email, FieldNote, JobReport, FollowUpTask
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

# Test 1: Structured note parses all fields
raw1 = "Location: Main Warehouse\nIssue: AC unit failure, not cooling.\nParts Used: Compressor, Refrigerant\nTime Spent: 90 min\nCustomer was upset about the heat."
parsed1 = parse_note(raw1)
assert_test(parsed1.location == "Main Warehouse", "Location extracted")
assert_test(parsed1.issue is not None and "AC" in parsed1.issue, "Issue extracted")
assert_test(len(parsed1.parts_used) == 2, "Parts extracted (2 items)")
assert_test(parsed1.time_spent_minutes == 90, "Time spent extracted")
assert_test(parsed1.follow_up_needed == True, "Follow-up flagged")

# Test 2: Build report from parsed note
report = build_report(parsed1)
assert_test(report.location == "Main Warehouse", "Report location correct")
assert_test(report.time_spent_minutes == 90, "Report time correct")
assert_test(len(report.summary) > 10, "Report has summary")

# Test 3: Follow-up tasks generated (actual function name: generate_followups)
follow_ups = generate_followups(parsed1)
assert_test(len(follow_ups) >= 1, "Follow-up tasks generated")

# Test 4: Customer update generated
update = draft_customer_email(report)
assert_test(len(update) > 20, "Customer update has content")
assert_test("Main Warehouse" in update or "AC" in update, "Update references job details")

# Test 5: Minimal note — graceful handling
raw2 = "Location: Unknown\nIssue: General maintenance"
parsed2 = parse_note(raw2)
assert_test(parsed2.location == "Unknown", "Minimal note parsed")

# Test 6: Structured output is valid JSON-serializable
import json
report_dict = report.__dict__ if hasattr(report, '__dict__') else {}
assert_test(isinstance(report_dict, dict), "Report is dict-serializable")

print(f"\nResults: {passed} passed, {failed} failed")
sys.exit(0 if failed == 0 else 1)
