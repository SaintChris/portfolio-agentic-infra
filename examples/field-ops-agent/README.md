# Field Operations Assistant Example — Portfolio Project

**Goal**: Turn messy field technician notes (and optional photo references) into a structured job record, generate follow‑up tasks, and draft a customer update email.

## Workflow
```
Unstructured Notes
      │
      ▼
┌─────────────────────┐
│ 1. PARSE NOTES      │ Extract key fields: location, issue, parts, time, sentiment
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│ 2. BUILD RECORD     │ `JobReport` JSON ready for DB insert
└───────┬─────────────┘
        │
        ▼
┌─────────────────────┐
│ 3. CREATE TASKS    │ Identify needed follow‑ups (order parts, schedule return, etc.)
└───────┬─────────────┘
        │
        ▼
┌─────────────────────┐
│ 4. DRAFT EMAIL     │ Customer update based on job outcome
└─────────────────────┘
```

## Files
- `README.md` – this overview and diagram
- `workflow.py` – runnable demo script (stdlib only)
- `templates/job-report-template.md` – markdown template for the structured report
- `templates/customer-update.md` – markdown template for the email draft

## Acceptance Criteria
- All four files exist in `examples/field-ops-agent/`
- `python3 workflow.py` runs clean and prints demo output for 3 sample notes
- Script demonstrates parsing, structuring, task generation, and email drafting
- README includes the ASCII workflow diagram above

## Output Location
`/Users/saint/github/portfolio-agentic-infra/examples/field-ops-agent/`
