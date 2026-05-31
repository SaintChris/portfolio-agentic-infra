# Executive Reporting Agent Example

**Goal**: Demonstrate an agent that pulls KPI data from multiple simulated sources, detects significant changes, correlates known events, generates a plain‑language executive brief, and ranks priorities.

## Workflow Diagram (ASCII)
```
+-----------------+   +-----------------+   +-----------------+
|  Data Sources   |   | Change Detection|   | Narrative &     |
|  (CRM, Finance, |-->| (Current vs     |-->| Prioritization  |
|   Support, …)   |   |  Previous)      |   | & Brief Output  |
+-----------------+   +-----------------+   +-----------------+
        |                     |                     |
        v                     v                     v
   +-----------+        +-----------+        +-----------------+
   | Simulated |        | Flagged   |        | `brief‑template` |
   |  Data     |        | Changes   |        |  Markdown       |
   +-----------+        +-----------+        +-----------------+
```

## Files
- `README.md` – This document.
- `workflow.py` – Runnable script (standard library only).
- `templates/brief-template.md` – Markdown template for the executive brief.
- `templates/data-sources.md` – Description of each simulated data source.

Run the example:
```bash
python3 workflow.py
```
The script prints a structured executive brief to the console.
