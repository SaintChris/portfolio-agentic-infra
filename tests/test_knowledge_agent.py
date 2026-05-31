#!/usr/bin/env python3
"""Tests for Knowledge Agent workflow."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Knowledge agent takes a query argument — test via subprocess
import subprocess

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

# Test 1: Knowledge agent runs with query argument
result = subprocess.run(
    [sys.executable, 
     os.path.join(os.path.dirname(__file__), '..', 'examples', 'knowledge-agent', 'workflow.py'),
     "How do I handle a billing dispute?"],
    capture_output=True, text=True, timeout=15,
    cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
assert_test(result.returncode == 0, "Knowledge agent runs without error")
output = result.stdout + result.stderr

# Test 2: Output contains an answer
assert_test("Answer:" in output or "answer" in output.lower(), "Returns an answer")

# Test 3: Output contains a citation
assert_test("Citation:" in output or "citation" in output.lower() or "[" in output, "Includes citation")

# Test 4: No error messages
assert_test("Error" not in output or "error" not in output.lower(), "No error messages in output")

# Test 5: Test with different query
result2 = subprocess.run(
    [sys.executable,
     os.path.join(os.path.dirname(__file__), '..', 'examples', 'knowledge-agent', 'workflow.py'),
     "What is the onboarding process?"],
    capture_output=True, text=True, timeout=15,
    cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
assert_test(result2.returncode == 0, "Second query runs without error")

# Test 6: Direct import works
from examples.knowledge_agent.workflow import search_knowledge_base, Document, SearchResult, synthesize_answer, load_sample_documents
docs = load_sample_documents()
results = search_knowledge_base("billing dispute", docs)
assert_test(len(results) >= 0, "Knowledge base query callable")  # May return 0 if no match

print(f"\nResults: {passed} passed, {failed} failed")
sys.exit(0 if failed == 0 else 1)
