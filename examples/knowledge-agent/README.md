# Knowledge Agent Example

**Purpose:** Demonstrate a lightweight knowledge agent that helps employees retrieve the right SOP, policy, customer context, or internal precedent without searching across ten systems.

## How it works

```
[Employee]  -->  Question
                |
                v
          Knowledge Agent
                |
                v
   Search across simulated docs
                |
                v
   Rank by relevance & recency
                |
                v
   Return answer + citation
```

- Documents are stored in a simple in‑memory index.
- Search is keyword‑overlap based (demo‑grade).
- Results are ranked by overlap count, source type priority, and recent date.
- The final answer includes a short human‑readable summary and a citation string like:
  `"[SOP] Employee Onboarding – Section 2 (2023-05-12)"`.

Run the agent with:
```
python3 workflow.py "How do I request vacation?"
```