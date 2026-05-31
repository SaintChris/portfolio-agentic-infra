#!/usr/bin/env python3
"""Tests for AI Intake Agent workflow."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from examples.intake_agent.workflow import (
    InboundRequest, classify_request, determine_routing,
    IssueCategory, Priority
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

# Test 1: Angry customer → human review
req = InboundRequest.from_email({
    "from": "angry@test.com",
    "subject": "Terrible service",
    "body": "This is the worst experience ever. I want to cancel everything."
})
classification = classify_request(req.body, req.subject)
assert_test(classification.sentiment == "angry", "Angry sentiment detected")
routing = determine_routing(classification)
assert_test(routing.action == "human_review", "Angry → human_review")

# Test 2: Critical → escalate
req2 = InboundRequest.from_email({
    "from": "ops@test.com",
    "subject": "Production down",
    "body": "URGENT: Production is down. All users affected."
})
classification2 = classify_request(req2.body, req2.subject)
assert_test(classification2.priority == Priority.CRITICAL, "CRITICAL priority")
routing2 = determine_routing(classification2)
assert_test(routing2.action == "escalate", "CRITICAL → escalate")

# Test 3: Billing question → correct classification
req3 = InboundRequest.from_email({
    "from": "billing@test.com",
    "subject": "Question about invoice",
    "body": "Hi, I have a question about my recent invoice charge."
})
classification3 = classify_request(req3.body, req3.subject)
assert_test(classification3.category == IssueCategory.BILLING, "Billing category")

# Test 4: Technical issue → correct classification
req4 = InboundRequest.from_email({
    "from": "dev@test.com",
    "subject": "Bug in dashboard",
    "body": "Getting an error when loading the dashboard. The page crashes."
})
classification4 = classify_request(req4.body, req4.subject)
assert_test(classification4.category == IssueCategory.TECHNICAL, "Technical category")

# Test 5: Low confidence → human review
classification_low = classify_request("Hi", "Hello")
assert_test(classification_low.confidence < 0.6, "Low confidence for vague input")
routing_low = determine_routing(classification_low)
assert_test(routing_low.action == "human_review", "Low confidence → human_review")

# Test 6: Never auto-send angry
angry_classification = classify_request(
    "This is terrible worst ever", "Complaint"
)
angry_routing = determine_routing(angry_classification)
assert_test(angry_routing.action != "auto_send", "Never auto-send angry")

print(f"\nResults: {passed} passed, {failed} failed")
sys.exit(0 if failed == 0 else 1)
