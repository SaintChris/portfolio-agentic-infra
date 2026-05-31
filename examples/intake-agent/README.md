# AI Intake Agent

**Example client project** — Built to demonstrate the kind of system I'd deploy at Rozeta Labs.

## What It Does

Reads inbound customer requests (email, form, chat), classifies the issue, pulls account context from multiple systems, drafts the right response, creates a follow-up task, routes exceptions to a human manager, and logs everything.

## Workflow

```
Inbound Request
      │
      ▼
┌─────────────────┐
│ 1. CLASSIFY     │  Issue type, urgency, sentiment
│    (LLM + rules)│  Output: category, priority, confidence
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. PULL CONTEXT │  CRM lookup, account history, past tickets
│    (API calls)  │  Output: customer profile, relevant history
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 3. DRAFT        │  Generate response using context + classification
│    (LLM)        │  Output: draft response, confidence score
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 4. ROUTE        │  High confidence → auto-send with audit log
│    (rules)      │  Medium → human review queue
│                 │  Low confidence / high priority → escalate to manager
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
 AUTO-SEND   HUMAN REVIEW
 + LOG       + TASK CREATED
```

## Tools Used

| Tool | Purpose |
|------|---------|
| Hermes Agent | Message routing, session memory, scheduling |
| Paperclip | Agent lifecycle, issue tracking |
| Zapier MCP | Gmail read/send, Google Drive, Slack notifications |
| Postgres | Ticket audit log, classification history |
| Qdrant | RAG lookup on past responses, SOP docs |
| Obsidian | Knowledge base of templates, escalation rules |

## Files

- `agent.md` — Agent configuration (skills, heartbeat, model)
- `workflow.py` — Core classification + routing logic
- `templates/response-generator.md` — Response drafting prompts
- `templates/escalation-policy.md` — When to escalate vs auto-send

## Real-World Metrics (from my personal deployment)

Running a simplified version of this for my own inbound Telegram/email:

| Metric | Value |
|--------|-------|
| Requests processed/day | 15-25 |
| Auto-resolution rate | ~60% |
| Escalation rate | ~15% |
| Avg response time | <2 min (vs 4-8 hours human) |
| Model cost | $0/day (free tier) |
