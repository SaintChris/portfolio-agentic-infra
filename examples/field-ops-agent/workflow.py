#!/usr/bin/env python3
"""Field Operations Assistant – Demo Workflow

Parses unstructured field technician notes into a structured job report, generates follow‑up tasks, and drafts a customer update email. Uses only the Python standard library.
"""

import json
import re
import datetime
from dataclasses import dataclass, asdict, field
from typing import List, Optional

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class FieldNote:
    raw: str
    # Extracted fields – optional because parsing may miss data
    location: Optional[str] = None
    issue: Optional[str] = None
    parts_used: List[str] = field(default_factory=list)
    time_spent_minutes: Optional[int] = None
    customer_sentiment: Optional[str] = None
    follow_up_needed: bool = False

@dataclass
class JobReport:
    location: str
    issue: str
    parts_used: List[str]
    time_spent_minutes: int
    summary: str
    timestamp: str = field(default_factory=lambda: datetime.datetime.now().isoformat())

@dataclass
class FollowUpTask:
    description: str
    due_in_days: int = 2
    assigned_to: str = "field_ops_lead"

# ---------------------------------------------------------------------------
# Simple parsing heuristics – look for "Location:", "Issue:", etc.
# ---------------------------------------------------------------------------

def _extract_line(prefix: str, text: str) -> Optional[str]:
    pattern = rf"{re.escape(prefix)}\s*(.*)"
    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return None

def parse_note(raw: str) -> FieldNote:
    note = FieldNote(raw=raw)
    note.location = _extract_line("Location:", raw)
    note.issue = _extract_line("Issue:", raw)
    parts = _extract_line("Parts Used:", raw)
    if parts:
        note.parts_used = [p.strip() for p in parts.split(",") if p.strip()]
    time = _extract_line("Time Spent:", raw)
    if time and time.isdigit():
        note.time_spent_minutes = int(time)
    elif time:
        # look for number of minutes in string
        m = re.search(r"(\d+)\s*min", time)
        if m:
            note.time_spent_minutes = int(m.group(1))
    # Sentiment – simple keywords
    lower = raw.lower()
    if any(w in lower for w in ["thank", "great", "appreciate"]):
        note.customer_sentiment = "positive"
    elif any(w in lower for w in ["bad", "angry", "frustrated", "unacceptable"]):
        note.customer_sentiment = "negative"
    else:
        note.customer_sentiment = "neutral"
    # Follow‑up needed if issue contains keywords like "break", "leak", "failure"
    if note.issue and any(w in note.issue.lower() for w in ["break", "leak", "failure", "replace"]):
        note.follow_up_needed = True
    return note

# ---------------------------------------------------------------------------
# Build report and tasks
# ---------------------------------------------------------------------------

def build_report(note: FieldNote) -> JobReport:
    # Fallback defaults if parsing missed data
    location = note.location or "Unknown location"
    issue = note.issue or "Unspecified issue"
    parts = note.parts_used or []
    time = note.time_spent_minutes or 0
    summary = f"Technician resolved '{issue}' at {location}."
    return JobReport(location=location, issue=issue, parts_used=parts, time_spent_minutes=time, summary=summary)

def generate_followups(note: FieldNote) -> List[FollowUpTask]:
    tasks: List[FollowUpTask] = []
    if note.follow_up_needed:
        tasks.append(FollowUpTask(description=f"Order replacement parts for issue: {note.issue}"))
        tasks.append(FollowUpTask(description="Schedule follow‑up visit to confirm fix", due_in_days=3))
    else:
        tasks.append(FollowUpTask(description="Close job – no further action required", due_in_days=0))
    return tasks

# ---------------------------------------------------------------------------
# Email draft using simple template strings
# ---------------------------------------------------------------------------

def draft_customer_email(report: JobReport) -> str:
    template = (
        "Subject: Update on your service request\n\n"
        "Hi [Customer],\n\n"
        "We have completed the work at {location}. The issue reported was '{issue}'.\n"
        "Parts used: {parts}.\n"
        "Time spent: {time} minutes.\n\n"
        "If you have any further questions or notice any new issues, please let us know.\n\n"
        "Thank you for choosing our service.\n"
        "Best regards,\n"
        "Field Operations Team"
    )
    parts_str = ", ".join(report.parts_used) if report.parts_used else "none"
    return template.format(
        location=report.location,
        issue=report.issue,
        parts=parts_str,
        time=report.time_spent_minutes,
    )

# ---------------------------------------------------------------------------
# Demo driver
# ---------------------------------------------------------------------------

def main():
    sample_notes = [
        """Location: Main Warehouse
Issue: Air conditioning unit failure, not cooling.
Parts Used: Compressor, Refrigerant
Time Spent: 90 min
Customer was upset about the heat.""",
        """Location: Site A - Roof
Issue: Minor roof leak after storm.
Parts Used: Sealant
Time Spent: 45 minutes
Customer thanked us for quick response.""",
        """Location: Office 3B
Issue: Light fixture flickering.
Time Spent: 30 mins
No parts needed.
Customer neutral.""",
    ]

    print("=" * 60)
    print("FIELD OPERATIONS ASSISTANT – Demo Run")
    print("=" * 60)

    for idx, raw in enumerate(sample_notes, 1):
        note = parse_note(raw)
        report = build_report(note)
        tasks = generate_followups(note)
        email = draft_customer_email(report)
        print(f"\n--- Sample #{idx} ---")
        print("Parsed Note:", json.dumps(asdict(note), indent=2))
        print("Job Report:", json.dumps(asdict(report), indent=2))
        print("Follow‑up Tasks:")
        for t in tasks:
            print("  -", t.description, f"(due in {t.due_in_days}d)")
        print("\nCustomer Email Draft:\n", email)
        print("-" * 40)

if __name__ == "__main__":
    main()
