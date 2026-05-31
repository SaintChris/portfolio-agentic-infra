# Approval Packet Template

**Packet ID:** {{packet_id}}
**Generated At:** {{generated_at}}

## Summary
- Total Invoices Processed: {{total_invoices}}
- Matched: {{matched_count}}
- Flagged: {{flagged_count}}
- Total Amount: ${{total_amount}}
- Flagged Amount: ${{flagged_amount}}

## Flagged Invoices
| Invoice ID | PO Number | Mismatch Type | Risk | Recommended Action |
|------------|-----------|---------------|------|--------------------|
{{#each mismatches}}
| {{invoice_id}} | {{po_number}} | {{type}} | {{risk}} | {{recommended_action}} |
{{/each}}

## Follow‑Up Drafts
{{#each follow_ups}}
**Invoice {{invoice_id}}** – {{mismatch_type}}
Subject: {{subject}}

{{body}}
---
{{/each}}

## Auto‑Approved
{{#each auto_approved}}
- Invoice {{invoice_id}} – ${{amount}}
{{/each}}

## Requires Manual Approval
{{#each requires_approval}}
- Invoice {{invoice_id}} – ${{amount}} ({{risk}} risk)
{{/each}}

**Notes:** {{notes}}
