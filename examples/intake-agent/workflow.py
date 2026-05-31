#!/usr/bin/env python3
"""
AI Intake Agent — Core Workflow
Classifies inbound requests, pulls context, drafts responses, routes to human or auto-send.

This is a standalone module that integrates with:
- Hermes Agent (message routing, memory)
- Paperclip (issue tracking, task creation)
- Zapier MCP (Gmail, Slack, Google Drive)
- Postgres (audit log, classification history)
- Qdrant (RAG on past responses, SOPs)
"""

import json
import hashlib
import datetime
from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import Optional


# ── Classification ──

class IssueCategory(Enum):
    TECHNICAL = "technical"
    BILLING = "billing"
    ACCOUNT = "account"
    GENERAL = "general"
    URGENT = "urgent"
    COMPLAINT = "complaint"


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Classification:
    category: IssueCategory
    priority: Priority
    confidence: float  # 0.0 - 1.0
    sentiment: str  # "positive", "neutral", "negative", "angry"
    summary: str
    keywords: list = field(default_factory=list)


# ── Inbound Request Model ──

@dataclass
class InboundRequest:
    id: str
    source: str  # "email", "form", "chat", "telegram"
    sender: str
    subject: str
    body: str
    received_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    raw: dict = field(default_factory=dict)

    @classmethod
    def from_email(cls, email_data: dict) -> "InboundRequest":
        content_hash = hashlib.md5(
            f"{email_data.get('from','')}{email_data.get('subject','')}{email_data.get('body','')}".encode()
        ).hexdigest()[:12]
        return cls(
            id=f"REQ-{content_hash}",
            source="email",
            sender=email_data.get("from", ""),
            subject=email_data.get("subject", ""),
            body=email_data.get("body", ""),
            raw=email_data,
        )


# ── Response Draft ──

@dataclass
class ResponseDraft:
    request_id: str
    body: str
    confidence: float
    requires_human_review: bool
    escalation_reason: Optional[str]
    suggested_actions: list = field(default_factory=list)
    context_used: list = field(default_factory=list)


# ── Routing Decision ──

@dataclass
class RoutingDecision:
    request_id: str
    action: str  # "auto_send", "human_review", "escalate"
    assigned_to: Optional[str]
    reason: str
    audit_log_id: Optional[str] = None


# ── Core Engine ──

INTAKE_AGENT_SYSTEM_PROMPT = """You are an AI Intake Agent for [CLIENT NAME].
Your job: read inbound customer requests, classify them, pull context, draft responses, and route appropriately.

CLASSIFICATION RULES:
- technical: bugs, errors, broken features, API issues
- billing: invoices, charges, refunds, payment failures
- account: login issues, profile changes, permissions
- complaint: expressing dissatisfaction, threats to churn
- urgent: time-sensitive, production down, data loss
- general: questions, feature requests, praise

PRIORITY RULES:
- CRITICAL: production down, data loss, security breach
- HIGH: paying customer blocked, billing error > $500
- MEDIUM: feature broken but workaround exists
- LOW: general questions, feature requests

ROUTING RULES:
- confidence ≥ 0.85 AND priority ≤ HIGH → auto_send
- confidence 0.6-0.85 OR sentiment == "angry" → human_review
- confidence < 0.6 OR priority == CRITICAL → escalate to manager
- ANY complaint → notify human (even if auto-sent)

ESCALATION POLICY:
- Never auto-send to angry customers
- Never auto-respond to CRITICAL issues
- Always create a task, even for auto-sends (for audit)
- Flag if same sender has 3+ requests in 7 days

You have access to these tools:
- search_past_responses(query) → Qdrant RAG lookup
- get_customer_profile(email) → CRM lookup
- get_recent_tickets(email) → Ticket history
- create_task(assignee, description) → Paperclip issue
- send_reply(email, body, draft_mode) → Gmail via Zapier
- notify_slack(channel, message) → Slack via Zapier
"""


def classify_request(body: str, subject: str) -> Classification:
    """
    Classification helper. In production, this is an LLM call.
    This version uses rule-based classification for demonstration.
    """
    text = f"{subject} {body}".lower()

    # Category detection
    category_scores = {}
    category_keywords = {
        IssueCategory.TECHNICAL: ["bug", "error", "broken", "not working", "crash", "failed", "issue", "problem"],
        IssueCategory.BILLING: ["invoice", "charge", "refund", "payment", "billing", "price", "cost", "subscription"],
        IssueCategory.ACCOUNT: ["login", "password", "reset", "account", "profile", "access", "locked"],
        IssueCategory.COMPLAINT: ["terrible", "worst", "unacceptable", "cancel", "refund", "lawyer", "complaint"],
        IssueCategory.URGENT: ["asap", "urgent", "immediately", "down", "outage", "critical", "emergency"],
        IssueCategory.GENERAL: ["question", "how", "what", "when", "feature", "request", "help", "thanks"],
    }
    for cat, keywords in category_keywords.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            category_scores[cat] = score

    if category_scores:
        category = max(category_scores, key=category_scores.get)
    else:
        category = IssueCategory.GENERAL

    # Priority detection
    if any(kw in text for kw in ["down", "outage", "emergency", "critical", "data loss"]):
        priority = Priority.CRITICAL
    elif any(kw in text for kw in ["urgent", "asap", "blocked", "can't access", "not working"]):
        priority = Priority.HIGH
    elif any(kw in text for kw in ["issue", "problem", "error", "bug"]):
        priority = Priority.MEDIUM
    else:
        priority = Priority.LOW

    # Sentiment (simplified)
    negative_words = ["terrible", "worst", "angry", "frustrated", "unacceptable", "disappointed", "cancel", "never"]
    positive_words = ["thanks", "great", "love", "awesome", "excellent", "good", "helpful"]
    neg_count = sum(1 for w in negative_words if w in text)
    pos_count = sum(1 for w in positive_words if w in text)

    if neg_count >= 2:
        sentiment = "angry"
    elif neg_count == 1:
        sentiment = "negative"
    elif pos_count > 0:
        sentiment = "positive"
    else:
        sentiment = "neutral"

    # Confidence: high if we matched multiple category keywords
    confidence = min(0.95, 0.5 + (category_scores.get(category, 0) * 0.1))

    # Summary (first 200 chars)
    summary = body[:200].replace("\n", " ").strip()

    return Classification(
        category=category,
        priority=priority,
        confidence=confidence,
        sentiment=sentiment,
        summary=summary,
        keywords=[kw for kw in sum(category_keywords.values(), []) if kw in text][:5],
    )


def determine_routing(classification: Classification) -> RoutingDecision:
    """Apply routing rules based on classification."""

    # CRITICAL → always escalate
    if classification.priority == Priority.CRITICAL:
        return RoutingDecision(
            request_id="",  # filled by caller
            action="escalate",
            assigned_to="manager",
            reason=f"CRITICAL priority issue: {classification.category.value}",
        )

    # Angry → always human review
    if classification.sentiment == "angry":
        return RoutingDecision(
            request_id="",
            action="human_review",
            assigned_to="support_lead",
            reason="Angry sentiment detected — human should review before sending",
        )

    # Low confidence → escalate
    if classification.confidence < 0.6:
        return RoutingDecision(
            request_id="",
            action="human_review",
            assigned_to="support_agent",
            reason=f"Low confidence ({classification.confidence:.2f}) — needs human review",
        )

    # Medium confidence → human review
    if classification.confidence < 0.85:
        return RoutingDecision(
            request_id="",
            action="human_review",
            assigned_to="support_agent",
            reason=f"Medium confidence ({classification.confidence:.2f})",
        )

    # High confidence, not critical, not angry → auto-send
    return RoutingDecision(
        request_id="",
        action="auto_send",
        assigned_to=None,
        reason=f"High confidence ({classification.confidence:.2f}), priority={classification.priority.name}",
    )


def process_request(request: InboundRequest) -> dict:
    """Full processing pipeline for a single inbound request."""

    # Step 1: Classify
    classification = classify_request(request.body, request.subject)

    # Step 2: Route
    routing = determine_routing(classification)
    routing.request_id = request.id

    # Step 3: Build decision record
    result = {
        "request": asdict(request),
        "classification": {
            "category": classification.category.value,
            "priority": classification.priority.name,
            "confidence": round(classification.confidence, 2),
            "sentiment": classification.sentiment,
            "summary": classification.summary,
            "keywords": classification.keywords,
        },
        "routing": {
            "action": routing.action,
            "assigned_to": routing.assigned_to,
            "reason": routing.reason,
        },
        "timestamp": datetime.datetime.now().isoformat(),
        "requires_human": routing.action != "auto_send",
    }

    return result


# ── Audit Logger ──

def log_to_audit(result: dict, db_connection=None) -> str:
    """Write processing result to audit log. Returns audit log entry ID."""
    audit_id = hashlib.md5(
        f"{result['request']['id']}{result['timestamp']}".encode()
    ).hexdigest()[:16]

    # In production, this writes to Postgres:
    # INSERT INTO intake_audit_log (id, request_id, action, classification, routed_to, timestamp)
    # VALUES (%s, %s, %s, %s, %s, %s)

    return audit_id


# ── Example Usage ──

if __name__ == "__main__":
    # Simulate processing 3 inbound requests
    test_requests = [
        InboundRequest.from_email({
            "from": "customer@example.com",
            "subject": "Can't login to my account",
            "body": "I've been trying to login for 30 minutes and it keeps saying password incorrect. I tried resetting but never got the email. This is urgent — I have a demo in an hour.",
        }),
        InboundRequest.from_email({
            "from": "angry@example.com",
            "subject": "Terrible service, want refund",
            "body": "This is the worst experience I've ever had. Your product broke our workflow and nobody responded to my last 3 emails. I want a full refund or I'm canceling everything.",
        }),
        InboundRequest.from_email({
            "from": "curious@example.com",
            "subject": "Question about pricing",
            "body": "Hi! I was wondering if you offer discounts for annual plans? Thanks, really loving the product so far.",
        }),
    ]

    print("=" * 60)
    print("AI INTAKE AGENT — Demo Run")
    print("=" * 60)

    for req in test_requests:
        result = process_request(req)
        print(f"\n📨 {req.id} | {req.sender}")
        print(f"   Subject: {req.subject[:60]}")
        print(f"   Category: {result['classification']['category']}")
        print(f"   Priority: {result['classification']['priority']}")
        print(f"   Sentiment: {result['classification']['sentiment']}")
        print(f"   Confidence: {result['classification']['confidence']}")
        print(f"   → Action: {result['routing']['action'].upper()}")
        print(f"   → Assigned: {result['routing']['assigned_to']}")
        print(f"   → Reason: {result['routing']['reason']}")
        print(f"   Needs human: {result['requires_human']}")
