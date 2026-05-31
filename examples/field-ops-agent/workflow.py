#!/usr/bin/env python3
import json
import re
from dataclasses import dataclass, asdict
from datetime import datetime

# Dataclasses
@dataclass
class FieldNote:
    raw: str
    location: str = ''
    issue: str = ''
    parts_used: list = None
    time_spent_minutes: int = 0
    customer_sentiment: str = ''
    follow_up_needed: bool = False

@dataclass
class JobReport:
    job_id: str
    location: str
    issue: str
    parts_used: list
    time_spent_minutes: int
    completed_at: str
    customer_sentiment: str

@dataclass
class FollowUpTask:
    description: str
    priority: str = 'medium'

# Sample notes (could be read from a file or stdin)
SAMPLE_NOTES = [
    "Customer at 123 Main St reported a leaking pipe. Used 2x 1/2" PVC pipe and sealant. Spent 45 minutes. Customer was upset but appreciative after fix.",
    "Site: 45 Oak Avenue. Broken window latch. Replaced latch. 30 mins. Customer happy.",
    "Location: 78 Pine Rd. Air conditioner not cooling. Checked filter, cleaned. 20 mins. Customer neutral.",
]

def parse_note(note: str) -> FieldNote:
    fn = FieldNote(raw=note)
    # Simple regex extractions
    loc_match = re.search(r'(?i)(?:at|site|location)[:\s]+([\d\w\s]+)', note)
    if loc_match:
        fn.location = loc_match.group(1).strip()
    issue_match = re.search(r'(?i)reported a ([^.]+)\. ', note)
    if not issue_match:
        issue_match = re.search(r'(?i)broken ([^.]+)\.', note)
    if issue_match:
        fn.issue = issue_match.group(1).strip()
    parts = re.findall(r'(?i)(\d+x?\s*[\w\-]+)', note)
    fn.parts_used = [p.strip() for p in parts] if parts else []
    time_match = re.search(r'(?i)(\d+)\s*minutes?', note)
    if time_match:
        fn.time_spent_minutes = int(time_match.group(1))
    sentiment_match = re.search(r'(?i)customer (upset|happy|neutral|satisfied)', note)
    if sentiment_match:
        fn.customer_sentiment = sentiment_match.group(1)
    fn.follow_up_needed = 'follow-up' in note.lower() or fn.parts_used
    return fn

def build_report(fn: FieldNote) -> JobReport:
    return JobReport(
        job_id=f"JOB-{int(datetime.utcnow().timestamp())}",
        location=fn.location,
        issue=fn.issue,
        parts_used=fn.parts_used,
        time_spent_minutes=fn.time_spent_minutes,
        completed_at=datetime.utcnow().isoformat() + 'Z',
        customer_sentiment=fn.customer_sentiment,
    )

def generate_follow_ups(fn: FieldNote) -> list:
    tasks = []
    if fn.parts_used:
        tasks.append(FollowUpTask(description="Order replacement parts: " + ", ".join(fn.parts_used)))
    if fn.follow_up_needed:
        tasks.append(FollowUpTask(description="Schedule follow‑up visit", priority='high'))
    return tasks

def render_template(report: JobReport) -> str:
    template = (
        "## Job Report\n"
        "- **Job ID:** {job_id}\n"
        "- **Location:** {location}\n"
        "- **Issue:** {issue}\n"
        "- **Parts Used:** {parts}\n"
        "- **Time Spent:** {time} minutes\n"
        "- **Completed At:** {completed}\n"
        "- **Customer Sentiment:** {sentiment}\n"
    )
    return template.format(
        job_id=report.job_id,
        location=report.location,
        issue=report.issue,
        parts=", ".join(report.parts_used) or "None",
        time=report.time_spent_minutes,
        completed=report.completed_at,
        sentiment=report.customer_sentiment or "N/A",
    )

def main():
    for note in SAMPLE_NOTES:
        fn = parse_note(note)
        report = build_report(fn)
        tasks = generate_follow_ups(fn)
        print(render_template(report))
        if tasks:
            print("### Follow‑up Tasks")
            for t in tasks:
                print(f"- [{t.priority}] {t.description}")
        print("---\n")

if __name__ == "__main__":
    main()
