#!/usr/bin/env python3
"""Tests for Finance Ops Agent workflow."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from examples.finance_ops_agent.workflow import (
    Invoice, PurchaseOrder, MismatchType, RiskLevel,
    reconcile_invoice, detect_duplicates, process_invoices
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

# Test 1: Matched invoice → no mismatches (use approved vendor)
po = PurchaseOrder("PO-001", "AWS Services", 100.00, "Test service", "2024-01-01", "Alex")
inv = Invoice("INV-001", "AWS Services", "PO-001", 100.00, 0.00, 100.00, "2024-01-05", "Test", "2024-02-05")
mismatches, is_matched = reconcile_invoice(inv, [po])
assert_test(is_matched == True, "Matched invoice → no mismatches")
assert_test(len(mismatches) == 0, "Zero mismatches for clean invoice")

# Test 2: Amount mismatch detected
inv2 = Invoice("INV-002", "AWS Services", "PO-001", 150.00, 0.00, 150.00, "2024-01-06", "Test", "2024-02-06")
mismatches2, is_matched2 = reconcile_invoice(inv2, [po])
amount_mm = [m for m in mismatches2 if m.type == MismatchType.AMOUNT_MISMATCH]
assert_test(len(amount_mm) == 1, "Amount mismatch detected")
assert_test(amount_mm[0].expected_value == "$100.00", "Expected value correct")
assert_test(amount_mm[0].actual_value == "$150.00", "Actual value correct")

# Test 3: Missing PO detected
inv3 = Invoice("INV-003", "TestVendor", "", 100.00, 0.00, 100.00, "2024-01-07", "Test", "2024-02-07")
mismatches3, _ = reconcile_invoice(inv3, [po])
missing_po = [m for m in mismatches3 if m.type == MismatchType.MISSING_PO]
assert_test(len(missing_po) >= 1, "Missing PO detected")

# Test 4: Duplicate detection
inv_a = Invoice("INV-A", "SameVendor", "PO-001", 200.00, 0.00, 200.00, "2024-01-10", "Test", "2024-02-10")
inv_b = Invoice("INV-B", "SameVendor", "PO-001", 200.00, 0.00, 200.00, "2024-01-15", "Test", "2024-02-15")
duplicates = detect_duplicates([inv_a, inv_b])
assert_test(len(duplicates) == 1, "Duplicate detected")
assert_test(duplicates[0].type == MismatchType.DUPLICATE_INVOICE, "Type is DUPLICATE_INVOICE")

# Test 5: Unknown vendor detected
inv5 = Invoice("INV-005", "ShadyCorp", "PO-001", 500.00, 0.00, 500.00, "2024-01-08", "Test", "2024-02-08")
mismatches5, _ = reconcile_invoice(inv5, [po])
unknown = [m for m in mismatches5 if m.type == MismatchType.UNKNOWN_VENDOR]
assert_test(len(unknown) >= 1, "Unknown vendor detected")
assert_test(unknown[0].risk == RiskLevel.HIGH, "Unknown vendor = HIGH risk")

# Test 6: Full pipeline generates packet with correct counts
test_invoices = [
    Invoice(f"INV-T{i}", "TestVendor", "PO-001", 100.00 + i * 10, 0, 100.00 + i * 10, f"2024-01-{10+i}", "Test", f"2024-02-{10+i}")
    for i in range(5)
]
test_pos = [PurchaseOrder("PO-001", "TestVendor", 100.00, "Test", "2024-01-01", "Alex")]
packet = process_invoices(test_invoices, test_pos)
assert_test(packet.total_invoices == 5, "Packet has 5 invoices")
assert_test(packet.flagged_count >= 1, "At least 1 flagged")
assert_test(len(packet.follow_ups) >= 1, "Follow-ups generated for flagged items")

print(f"\nResults: {passed} passed, {failed} failed")
sys.exit(0 if failed == 0 else 1)
