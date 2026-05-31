# Finance Ops Agent

**Example client project** — Reconciles invoices, flags mismatches, drafts vendor follow-ups, prepares approval packets.

## What It Does

Reads invoices from accounting software or CSV export, matches each against purchase orders, detects mismatches (amount, duplicates, missing PO, unknown vendor), drafts professional follow-up emails, and assembles an approval packet for finance team review.

## Workflow

```
Invoice Import (CSV / API)
         │
         ▼
┌──────────────────┐
│ 1. PARSE         │  Extract vendor, amount, date, PO number, line items
│ (CSV/API)        │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ 2. RECONCILE     │  Match against PO database
│ (matching logic) │  Check: amount, vendor, date range, PO exists
└────────┬─────────┘
         │
    ┌────┴────┐
    ▼         ▼
 MATCHED    MISMATCH
    │         │
    │    ┌────┴────────────────────┐
    │    ▼           ▼            ▼
    │  AMOUNT     DUPLICATE    MISSING PO
    │  MISMATCH   INVOICE      /UNKNOWN
    │    │           │         VENDOR
    │    └────┬──────┘         │
    │         ▼               │
    │   DRAFT FOLLOW-UP       │
    └─────────┬───────────────┘
              ▼
    ┌──────────────────┐
    │ 3. APPROVAL      │  Bundle all flagged items into decision-ready packet
    │ PACKET           │  Risk-ranked, with recommended actions
    └────────┬─────────┘
              ▼
    ┌──────────────────┐
    │ 4. ROUTE         │  Auto-approve if under threshold + clean history
    │                  │  Route to manager if over threshold or high risk
    │                  │  Block payment if fraud indicators
    └──────────────────┘
```

## Mismatch Types Detected

| Type | Description | Risk | Auto-Action |
|------|-------------|------|-------------|
| Amount Mismatch | Invoice ≠ PO amount | Medium | Flag + draft follow-up |
| Duplicate Invoice | Same vendor+amount+date within 30 days | High | Block + flag for review |
| Missing PO | No PO found for invoice | Medium | Request PO from requestor |
| Unknown Vendor | Vendor not in approved list | High | Block + notify procurement |
| Over Threshold | Amount exceeds approval limit | Medium | Route to next-level approver |
| Tax Mismatch | Tax calculation incorrect | Low | Auto-calculate correct amount |

## Tools Used

| Tool | Purpose |
|------|---------|
| Zapier MCP | Gmail (draft/send), Google Drive (PO storage), Google Sheets |
| Paperclip | Approval task tracking, audit trail |
| Postgres | Invoice history, vendor database, approval log |
| Qdrant | Vendor history lookup, past mismatch patterns |
| Hermes Agent | Scheduling, memory, Telegram notifications |

## Metrics (from personal deployment)

Running a version of this against my own bank statements and financial data:

| Metric | Value |
|--------|-------|
| Transactions analyzed | 753 across 4 accounts, ~34 months |
| Invoices processed/month | ~50-80 (business + personal) |
| Mismatch detection rate | ~12-15% flagged for review |
| False positive rate | ~3% |
| Time savings | ~4-6 hours/month manual reconciliation |
| Model cost | $0/month (free tier) |
