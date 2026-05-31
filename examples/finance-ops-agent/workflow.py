#!/usr/bin/env python3
"""
Finance Ops Agent — Invoice Reconciliation & Approval Pipeline
Reconciles invoices against POs, flags mismatches, drafts vendor follow-ups,
prepares approval packets.

Dependencies: Python 3.9+ stdlib only.
Run: python3 workflow.py
"""

import csv
import io
import hashlib
import datetime
from enum import Enum
from dataclasses import dataclass, field
from typing import Optional


# ── Models ──

class MismatchType(Enum):
    AMOUNT_MISMATCH = "amount_mismatch"
    DUPLICATE_INVOICE = "duplicate_invoice"
    MISSING_PO = "missing_po"
    UNKNOWN_VENDOR = "unknown_vendor"
    OVER_THRESHOLD = "over_threshold"
    TAX_MISMATCH = "tax_mismatch"


class RiskLevel(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class PurchaseOrder:
    po_number: str
    vendor: str
    amount: float
    description: str
    date: str
    approved_by: str
    status: str = "open"  # open, fulfilled, cancelled


@dataclass
class Invoice:
    invoice_id: str
    vendor: str
    po_number: str
    amount: float
    tax: float
    total: float
    date: str
    description: str
    due_date: str
    status: str = "pending"  # pending, matched, flagged, approved, rejected


@dataclass
class Mismatch:
    invoice_id: str
    po_number: str
    type: MismatchType
    risk: RiskLevel
    description: str
    expected_value: Optional[str]
    actual_value: Optional[str]
    recommended_action: str


@dataclass
class FollowUp:
    invoice_id: str
    vendor: str
    mismatch_type: MismatchType
    subject: str
    body: str
    priority: str  # low, normal, high, urgent


@dataclass
class ApprovalPacket:
    packet_id: str
    generated_at: str
    total_invoices: int
    matched_count: int
    flagged_count: int
    total_amount: float
    flagged_amount: float
    mismatches: list
    follow_ups: list
    auto_approved: list
    requires_approval: list
    notes: str


# ── Sample Data ──

SAMPLE_POS = [
    PurchaseOrder("PO-2024-001", "AWS Services", 1200.00, "Cloud hosting Q1", "2024-01-15", "Alex"),
    PurchaseOrder("PO-2024-002", "Google LLC", 450.00, "Google Workspace annual", "2024-02-01", "Alex"),
    PurchaseOrder("PO-2024-003", "GitHub Inc", 240.00, "GitHub Teams annual", "2024-02-10", "Alex"),
    PurchaseOrder("PO-2024-004", "OpenRouter", 500.00, "API credits Q1", "2024-03-01", "Alex"),
    PurchaseOrder("PO-2024-005", "DigitalOcean", 180.00, "VPS hosting", "2024-03-05", "Alex"),
]

SAMPLE_INVOICES = [
    Invoice("INV-001", "AWS Services", "PO-2024-001", 1200.00, 0.00, 1200.00, "2024-01-20", "Cloud hosting Q1", "2024-02-20"),
    Invoice("INV-002", "Google LLC", "PO-2024-002", 489.99, 0.00, 489.99, "2024-02-05", "Google Workspace", "2024-03-05"),
    Invoice("INV-003", "GitHub Inc", "PO-2024-003", 240.00, 0.00, 240.00, "2024-02-12", "GitHub Teams", "2024-03-12"),
    Invoice("INV-004", "AWS Services", "PO-2024-001", 1200.00, 0.00, 1200.00, "2024-01-22", "Cloud hosting Q1 duplicate", "2024-02-22"),
    Invoice("INV-005", "UnknownSoft Corp", "", 3500.00, 280.00, 3780.00, "2024-03-10", "Software license", "2024-04-10"),
    Invoice("INV-006", "DigitalOcean", "PO-2024-005", 194.99, 0.00, 194.99, "2024-03-08", "VPS hosting + bandwidth", "2024-04-08"),
    Invoice("INV-007", "OpenRouter", "PO-2024-004", 500.00, 0.00, 500.00, "2024-03-02", "API credits Q1", "2024-04-02"),
]

APPROVAL_THRESHOLD = 500.00  # Auto-approve under this amount
APPROVED_VENDORS = {"AWS Services", "Google LLC", "GitHub Inc", "OpenRouter", "DigitalOcean"}


# ── Reconciliation Engine ──

def reconcile_invoice(invoice: Invoice, pos: list) -> tuple:
    """
    Reconcile a single invoice against PO database.
    Returns (mismatches_list, is_matched).
    """
    mismatches = []

    # Check 1: Vendor validation
    if invoice.vendor not in APPROVED_VENDORS:
        mismatches.append(Mismatch(
            invoice_id=invoice.invoice_id,
            po_number=invoice.po_number,
            type=MismatchType.UNKNOWN_VENDOR,
            risk=RiskLevel.HIGH,
            description=f"Vendor '{invoice.vendor}' not in approved vendor list",
            expected_value=str(list(APPROVED_VENDORS)),
            actual_value=invoice.vendor,
            recommended_action="Block payment. Contact procurement to validate vendor.",
        ))

    # Check 2: PO existence
    if not invoice.po_number:
        mismatches.append(Mismatch(
            invoice_id=invoice.invoice_id,
            po_number="",
            type=MismatchType.MISSING_PO,
            risk=RiskLevel.MEDIUM,
            description="No purchase order number on invoice",
            expected_value="PO number required",
            actual_value="(empty)",
            recommended_action="Request PO from invoice requestor before payment.",
        ))
    else:
        # Find matching PO
        matching_po = next((po for po in pos if po.po_number == invoice.po_number), None)

        if matching_po is None:
            mismatches.append(Mismatch(
                invoice_id=invoice.invoice_id,
                po_number=invoice.po_number,
                type=MismatchType.MISSING_PO,
                risk=RiskLevel.MEDIUM,
                description=f"PO {invoice.po_number} not found in system",
                expected_value="Valid PO number",
                actual_value=invoice.po_number,
                recommended_action="Verify PO number with requestor.",
            ))
        else:
            # Check 3: Amount match
            if abs(invoice.amount - matching_po.amount) > 0.01:
                mismatches.append(Mismatch(
                    invoice_id=invoice.invoice_id,
                    po_number=invoice.po_number,
                    type=MismatchType.AMOUNT_MISMATCH,
                    risk=RiskLevel.MEDIUM,
                    description=f"Invoice amount differs from PO",
                    expected_value=f"${matching_po.amount:.2f}",
                    actual_value=f"${invoice.amount:.2f}",
                    recommended_action="Draft vendor follow-up requesting corrected invoice or PO amendment.",
                ))

            # Check 4: Vendor-PO match
            if invoice.vendor != matching_po.vendor:
                mismatches.append(Mismatch(
                    invoice_id=invoice.invoice_id,
                    po_number=invoice.po_number,
                    type=MismatchType.UNKNOWN_VENDOR,
                    risk=RiskLevel.HIGH,
                    description=f"Invoice vendor doesn't match PO vendor",
                    expected_value=matching_po.vendor,
                    actual_value=invoice.vendor,
                    recommended_action="URGENT: Potential fraud. Do not pay until verified.",
                ))

            # Check 5: PO status
            if matching_po.status == "cancelled":
                mismatches.append(Mismatch(
                    invoice_id=invoice.invoice_id,
                    po_number=invoice.po_number,
                    type=MismatchType.MISSING_PO,
                    risk=RiskLevel.HIGH,
                    description=f"PO {invoice.po_number} was cancelled",
                    expected_value="Active PO",
                    actual_value="Cancelled PO",
                    recommended_action="Reject invoice. PO was cancelled.",
                ))

    # Check 6: Over threshold
    if invoice.total > APPROVAL_THRESHOLD and not mismatches:
        # Only flag if otherwise clean (mismatches already caught above)
        pass  # This is normal for large items — just needs approval routing

    is_matched = len(mismatches) == 0
    return mismatches, is_matched


def detect_duplicates(invoices: list) -> list:
    """Detect potential duplicate invoices (same vendor + amount within 30 days)."""
    duplicates = []
    seen = {}
    for inv in invoices:
        key = (inv.vendor, inv.amount)
        if key in seen:
            prev = seen[key]
            try:
                d1 = datetime.date.fromisoformat(inv.date)
                d2 = datetime.date.fromisoformat(prev.date)
                if abs((d1 - d2).days) <= 30:
                    duplicates.append(Mismatch(
                        invoice_id=inv.invoice_id,
                        po_number=inv.po_number,
                        type=MismatchType.DUPLICATE_INVOICE,
                        risk=RiskLevel.HIGH,
                        description=f"Potential duplicate of {prev.invoice_id} (same vendor + amount within 30 days)",
                        expected_value=f"Original: {prev.invoice_id} on {prev.date}",
                        actual_value=f"Duplicate: {inv.invoice_id} on {inv.date}",
                        recommended_action="Verify with vendor. If duplicate, reject and flag for audit.",
                    ))
            except ValueError:
                pass
        else:
            seen[key] = inv
    return duplicates


def draft_follow_up(mismatch: Mismatch, invoices: list) -> FollowUp:
    """Generate a follow-up email draft for a mismatch."""

    invoice = next((i for i in invoices if i.invoice_id == mismatch.invoice_id), None)
    vendor = invoice.vendor if invoice else "Vendor"

    templates = {
        MismatchType.AMOUNT_MISMATCH: {
            "subject": f"Invoice {mismatch.invoice_id} — Amount Discrepancy",
            "body": f"""Dear {vendor} Accounts Receivable,

We received invoice {mismatch.invoice_id} for ${invoice.total if invoice else 'N/A':.2f} dated {invoice.date if invoice else 'N/A'}.

Upon reconciliation, we noticed a discrepancy with the corresponding purchase order ({mismatch.po_number}):
- PO amount: {mismatch.expected_value}
- Invoice amount: {mismatch.actual_value}

Could you please issue a corrected invoice or confirm the correct amount?

Thank you,
Finance Operations""",
            "priority": "normal",
        },
        MismatchType.DUPLICATE_INVOICE: {
            "subject": f"Invoice {mismatch.invoice_id} — Possible Duplicate",
            "body": f"""Dear {vendor} Accounts Receivable,

We believe invoice {mismatch.invoice_id} may be a duplicate of a previously processed payment.

{mismatch.description}

Before we process this invoice, could you please confirm this is a new charge and not a resubmission?

Thank you,
Finance Operations""",
            "priority": "high",
        },
        MismatchType.MISSING_PO: {
            "subject": f"Invoice {mismatch.invoice_id} — Missing Purchase Order",
            "body": f"""Dear {vendor} Accounts Receivable,

We received invoice {mismatch.invoice_id} but cannot locate the corresponding purchase order in our system.

Please provide the correct PO number or confirm which department requested this service so we can locate the authorization.

Thank you,
Finance Operations""",
            "priority": "normal",
        },
        MismatchType.UNKNOWN_VENDOR: {
            "subject": f"Invoice {mismatch.invoice_id} — Vendor Verification Required",
            "body": f"""Dear {vendor} Accounts Receivable,

Invoice {mismatch.invoice_id} is from a vendor not currently in our approved supplier list.

Please provide:
- Tax ID / Business registration
- Signed W-9 form
- Contact information for our procurement team

We will process payment once vendor onboarding is complete.

Thank you,
Finance Operations""",
            "priority": "urgent",
        },
    }

    template = templates.get(mismatch.type, {
        "subject": f"Invoice {mismatch.invoice_id} — Review Required",
        "body": f"Invoice {mismatch.invoice_id} requires manual review.\n\nIssue: {mismatch.description}\n\nRecommended action: {mismatch.recommended_action}",
        "priority": "normal",
    })

    return FollowUp(
        invoice_id=mismatch.invoice_id,
        vendor=vendor,
        mismatch_type=mismatch.type,
        subject=template["subject"],
        body=template["body"],
        priority=template["priority"],
    )


def build_approval_packet(invoices: list, all_mismatches: list, follow_ups: list) -> ApprovalPacket:
    """Build the approval packet summarizing all flagged items."""

    matched = [i for i in invoices if not any(m.invoice_id == i.invoice_id for m in all_mismatches)]
    flagged = [i for i in invoices if any(m.invoice_id == i.invoice_id for m in all_mismatches)]

    # Auto-approve matched invoices under threshold
    auto_approved = [i for i in matched if i.total <= APPROVAL_THRESHOLD]
    needs_approval = [i for i in matched if i.total > APPROVAL_THRESHOLD] + flagged

    total_amount = sum(i.total for i in invoices)
    flagged_amount = sum(i.total for i in flagged)

    packet_id = hashlib.md5(
        f"{len(invoices)}{datetime.datetime.now().isoformat()}".encode()
    ).hexdigest()[:10]

    notes = []
    if flagged:
        high_risk = [m for m in all_mismatches if m.risk == RiskLevel.HIGH]
        if high_risk:
            notes.append(f"⚠ {len(high_risk)} HIGH RISK items require immediate attention")
        notes.append(f"Follow-up drafts prepared for {len(follow_ups)} flagged invoices")
    else:
        notes.append("All invoices matched clean — no mismatches detected")

    return ApprovalPacket(
        packet_id=f"PKT-{packet_id}",
        generated_at=datetime.datetime.now().isoformat(),
        total_invoices=len(invoices),
        matched_count=len(matched),
        flagged_count=len(flagged),
        total_amount=total_amount,
        flagged_amount=flagged_amount,
        mismatches=all_mismatches,
        follow_ups=follow_ups,
        auto_approved=auto_approved,
        requires_approval=needs_approval,
        notes=" | ".join(notes),
    )


def process_invoices(invoices: list, pos: list) -> ApprovalPacket:
    """Full reconciliation pipeline."""

    all_mismatches = []

    # Reconcile each invoice
    for invoice in invoices:
        mismatches, _ = reconcile_invoice(invoice, pos)
        all_mismatches.extend(mismatches)

    # Detect duplicates
    duplicates = detect_duplicates(invoices)
    all_mismatches.extend(duplicates)

    # Draft follow-ups
    follow_ups = []
    seen_invoices = set()
    for m in all_mismatches:
        if m.invoice_id not in seen_invoices:
            follow_ups.append(draft_follow_up(m, invoices))
            seen_invoices.add(m.invoice_id)

    # Build packet
    packet = build_approval_packet(invoices, all_mismatches, follow_ups)

    return packet


def print_packet(packet: ApprovalPacket):
    """Pretty-print the approval packet to console."""

    print("=" * 70)
    print(f"  FINANCE OPS AGENT — Approval Packet {packet.packet_id}")
    print(f"  Generated: {packet.generated_at}")
    print("=" * 70)

    print(f"\n📊 SUMMARY")
    print(f"   Total invoices:  {packet.total_invoices}")
    print(f"   Total amount:    ${packet.total_amount:,.2f}")
    print(f"   Matched clean:   {packet.matched_count}")
    print(f"   Flagged:         {packet.flagged_count}")
    print(f"   Flagged amount:  ${packet.flagged_amount:,.2f}")
    print(f"   Auto-approved:   {len(packet.auto_approved)}")
    print(f"   Need approval:   {len(packet.requires_approval)}")

    if packet.notes:
        print(f"\n📝 Notes: {packet.notes}")

    if packet.mismatches:
        print(f"\n⚠ MISMATCHES DETECTED ({len(packet.mismatches)})")
        print("-" * 70)
        for m in packet.mismatches:
            risk_icon = {"low": "🟢", "medium": "🟡", "high": "🔴"}[m.risk.value]
            print(f"\n   {risk_icon} [{m.risk.value.upper()}] {m.type.value}")
            print(f"      Invoice:  {m.invoice_id}")
            print(f"      PO:       {m.po_number or '(none)'}")
            print(f"      Issue:    {m.description}")
            if m.expected_value:
                print(f"      Expected: {m.expected_value}")
                print(f"      Actual:   {m.actual_value}")
            print(f"      Action:   {m.recommended_action}")

    if packet.follow_ups:
        print(f"\n📧 FOLLOW-UP DRAFTS ({len(packet.follow_ups)})")
        print("-" * 70)
        for fu in packet.follow_ups:
            print(f"\n   → {fu.subject}")
            print(f"     Vendor: {fu.vendor} | Priority: {fu.priority}")
            print(f"     Preview: {fu.body[:120]}...")

    if packet.auto_approved:
        print(f"\n✅ AUTO-APPROVED ({len(packet.auto_approved)})")
        print("-" * 70)
        for inv in packet.auto_approved:
            print(f"   {inv.invoice_id} | {inv.vendor:<20} | ${inv.total:>10,.2f} | {inv.description}")

    if packet.requires_approval:
        print(f"\n👤 REQUIRES APPROVAL ({len(packet.requires_approval)})")
        print("-" * 70)
        for inv in packet.requires_approval:
            flag_reason = next(
                (m.description for m in packet.mismatches if m.invoice_id == inv.invoice_id),
                "Over approval threshold"
            )
            print(f"   {inv.invoice_id} | {inv.vendor:<20} | ${inv.total:>10,.2f} | {flag_reason}")

    print(f"\n{'=' * 70}")
    print(f"  Packet {packet.packet_id} ready for review")
    print(f"{'=' * 70}")


# ── Run ──

if __name__ == "__main__":
    print("\n🏦 FINANCE OPS AGENT — Invoice Reconciliation Pipeline\n")
    print(f"Processing {len(SAMPLE_INVOICES)} invoices against {len(SAMPLE_POS)} purchase orders...\n")

    packet = process_invoices(SAMPLE_INVOICES, SAMPLE_POS)
    print_packet(packet)
