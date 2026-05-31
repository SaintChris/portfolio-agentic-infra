#!/usr/bin/env python3
"""
Human Review Queue Pattern
==========================
Human-in-the-loop review queue with SLA tracking, priority levels,
auto-escalation, and review quality metrics.

Demonstrates the Rozeta job requirement:
  "AI drafts, recommends, routes — but humans remain in control
   where judgment matters."

In production: backed by Postgres. Demo uses JSON storage.
"""

import json, hashlib, datetime, os, time
from dataclasses import dataclass, field, asdict
from typing import List, Optional
from enum import Enum


class Priority(Enum):
    LOW = "low"; MEDIUM = "medium"; HIGH = "high"; CRITICAL = "critical"

class Status(Enum):
    PENDING = "pending"; APPROVED = "approved"; REJECTED = "rejected"
    ESCALATED = "escalated"

SLA_HOURS = {Priority.LOW: 48, Priority.MEDIUM: 24, Priority.HIGH: 4, Priority.CRITICAL: 1}


@dataclass
class ReviewItem:
    id: str; agent: str; content_type: str; content: str
    priority: Priority; status: Status = Status.PENDING
    assigned_to: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    reviewed_at: Optional[str] = None; reviewer_notes: Optional[str] = None
    sla_hours: int = 0

    def __post_init__(self):
        if not self.sla_hours:
            self.sla_hours = SLA_HOURS.get(self.priority, 24)

    @property
    def is_sla_breached(self) -> bool:
        if self.status in (Status.APPROVED, Status.REJECTED): return False
        return datetime.datetime.now() > datetime.datetime.fromisoformat(
            (datetime.datetime.fromisoformat(self.created_at) + datetime.timedelta(hours=self.sla_hours)).isoformat()
        )

    @property
    def hours_remaining(self) -> float:
        deadline = datetime.datetime.fromisoformat(self.created_at) + datetime.timedelta(hours=self.sla_hours)
        return max(0, (deadline - datetime.datetime.now()).total_seconds() / 3600)


@dataclass
class ReviewQueue:
    path: str = ""
    items: List[ReviewItem] = field(default_factory=list)

    def __post_init__(self):
        if not self.path:
            self.path = os.path.join(os.path.dirname(__file__), "review_queue.json")
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            with open(self.path) as f:
                data = json.load(f)
            raw_items = data.get("items", [])
            self.items = []
            for i in raw_items:
                i['priority'] = Priority(i.get('priority', 'medium'))
                i['status'] = Status(i.get('status', 'pending'))
                self.items.append(ReviewItem(**i))

    def _serialize_item(self, item):
        d = asdict(item)
        d['priority'] = item.priority.value
        d['status'] = item.status.value
        return d

    def _save(self):
        with open(self.path, "w") as f:
            json.dump({"items": [self._serialize_item(i) for i in self.items]}, f, indent=2)

    def submit(self, agent, content_type, content, priority=Priority.MEDIUM) -> ReviewItem:
        item = ReviewItem(
            id=f"REV-{hashlib.md5(f'{agent}{time.time()}'.encode()).hexdigest()[:8]}",
            agent=agent, content_type=content_type, content=content[:200], priority=priority
        )
        self.items.append(item)
        self._save()
        return item

    def pending(self) -> List[ReviewItem]:
        return sorted([i for i in self.items if i.status == Status.PENDING],
                      key=lambda i: i.hours_remaining)

    def review(self, item_id, decision, reviewer, notes=""):
        item = next((i for i in self.items if i.id == item_id), None)
        if item:
            item.status = Status(decision) if decision in [s.value for s in Status] else Status.APPROVED
            item.reviewed_at = datetime.datetime.now().isoformat()
            item.reviewer_notes = notes
            self._save()
        return item

    def check_sla(self) -> List[ReviewItem]:
        breached = [i for i in self.items if i.is_sla_breached and i.status == Status.PENDING]
        for i in breached:
            i.status = Status.ESCALATED
        if breached:
            self._save()
        return breached

    def stats(self) -> dict:
        return {
            "total": len(self.items),
            "pending": len([i for i in self.items if i.status == Status.PENDING]),
            "approved": len([i for i in self.items if i.status == Status.APPROVED]),
            "rejected": len([i for i in self.items if i.status == Status.REJECTED]),
            "escalated": len([i for i in self.items if i.status == Status.ESCALATED]),
        }


if __name__ == "__main__":
    q = ReviewQueue(os.path.join(os.path.dirname(__file__), "review_queue.json"))

    # Simulate submitting AI outputs for review
    q.submit("intake_agent", "email_draft",
             "Dear customer, we're sorry to hear about the issue...",
             Priority.HIGH)
    q.submit("finance_agent", "approval_packet",
             "PKT-001: 3 invoices flagged, $2,450 total",
             Priority.MEDIUM)
    q.submit("content_agent", "linkedin_post",
             "I built 5 AI agents that actually work...",
             Priority.LOW)

    # Check SLA breaches
    breached = q.check_sla()
    if breached:
        print(f"⚠ {len(breached)} items breached SLA and were escalated")

    # Show queue
    stats = q.stats()
    print(f"\n{'='*50}")
    print(f"  HUMAN REVIEW QUEUE")
    print(f"{'='*50}")
    print(f"  Total: {stats['total']} | Pending: {stats['pending']} | "
          f"Approved: {stats['approved']} | Rejected: {stats['rejected']} | "
          f"Escalated: {stats['escalated']}")

    print(f"\nPending items (sorted by SLA urgency):")
    for item in q.pending():
        print(f"  {item.id} | {item.agent:<20} | {item.priority.value:<8} | "
              f"{item.hours_remaining:.1f}h remaining | {item.content_type}")

    # Simulate a review
    if q.pending():
        first = q.pending()[0]
        q.review(first.id, "approved", "alex", "Looks good, ship it")
        print(f"\n✓ Reviewed {first.id}: approved by alex")

    print(f"\nFinal stats: {q.stats()}")
