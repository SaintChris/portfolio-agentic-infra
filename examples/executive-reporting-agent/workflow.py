import random
import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Any

# ---------- Simulated Data Sources ----------

def simulate_crm() -> Dict[str, float]:
    return {
        "deals": random.randint(80, 120),
        "pipeline": random.randint(300, 500),
        "win_rate": round(random.uniform(0.2, 0.4), 3),
        "churn": round(random.uniform(0.01, 0.05), 3),
    }

def simulate_finance() -> Dict[str, float]:
    return {
        "mrr": random.randint(50000, 80000),
        "burn": random.randint(15000, 25000),
        "ar_aging": random.randint(10, 30),
    }

def simulate_support() -> Dict[str, float]:
    return {
        "tickets": random.randint(200, 350),
        "resolution_time": round(random.uniform(2, 5), 2),
        "csat": round(random.uniform(3.5, 4.7), 2),
    }

def simulate_projects() -> Dict[str, float]:
    return {
        "milestones": random.randint(5, 9),
        "completion_pct": random.randint(60, 90),
    }

def simulate_custom() -> Dict[str, float]:
    return {
        "active_users": random.randint(1500, 2500),
        "feature_adoption": round(random.uniform(0.3, 0.7), 3),
    }

# ---------- Change Detection ----------

def compute_changes(prev: Dict[str, float], curr: Dict[str, float]) -> Dict[str, Dict[str, Any]]:
    changes = {}
    for key, curr_val in curr.items():
        prev_val = prev.get(key, 0)
        if isinstance(curr_val, (int, float)) and prev_val != 0:
            pct_change = (curr_val - prev_val) / prev_val * 100
        else:
            pct_change = 0
        changes[key] = {
            "prev": prev_val,
            "curr": curr_val,
            "pct_change": round(pct_change, 2),
            "significant": abs(pct_change) >= 10,
        }
    return changes

# ---------- Known Events ----------
KNOWN_EVENTS = [
    {"name": "v2.3 released", "impact": {"tickets": 30, "feature_adoption": 5}},
    {"name": "pricing update", "impact": {"mrr": 8, "win_rate": -5}},
]

def correlate_events(changes: Dict[str, Dict[str, Any]]) -> List[str]:
    correlated = []
    for event in KNOWN_EVENTS:
        for metric, impact in event["impact"].items():
            if metric in changes and changes[metric]["pct_change"] * impact > 0:
                correlated.append(event["name"])  # simple correlation
                break
    return list(set(correlated))

# ---------- Narrative Generation ----------

def generate_sentences(changes: Dict[str, Dict[str, Any]]) -> List[str]:
    sentences = []
    for metric, info in changes.items():
        if info["significant"]:
            direction = "increased" if info["pct_change"] > 0 else "decreased"
            sentences.append(f"{metric.replace('_', ' ').title()} {direction} by {abs(info['pct_change'])}% (from {info['prev']} to {info['curr']}).")
    if not sentences:
        sentences.append("No significant metric changes detected this period.")
    return sentences

# ---------- Data Model ----------

@dataclass
class ExecutiveBrief:
    date: str
    headline: str
    insights: List[str] = field(default_factory=list)
    correlated_events: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metrics_table: str = ""

    def format(self) -> str:
        from pathlib import Path
        template_path = Path(__file__).parent / "templates" / "brief-template.md"
        template = template_path.read_text()
        return template.format(
            date=self.date,
            headline=self.headline,
            insights="\n".join(f"- {s}" for s in self.insights),
            events=", ".join(self.correlated_events) if self.correlated_events else "None",
            recommendations="\n".join(f"- {r}" for r in self.recommendations),
            metrics=self.metrics_table,
        )

# ---------- Main Execution ----------

def main():
    # Simulate previous period
    random.seed(42)  # deterministic for demo
    prev = {
        **simulate_crm(),
        **simulate_finance(),
        **simulate_support(),
        **simulate_projects(),
        **simulate_custom(),
    }
    # Simulate current period (different seed)
    random.seed(datetime.datetime.now().timestamp())
    curr = {
        **simulate_crm(),
        **simulate_finance(),
        **simulate_support(),
        **simulate_projects(),
        **simulate_custom(),
    }

    changes = compute_changes(prev, curr)
    events = correlate_events(changes)
    insights = generate_sentences(changes)

    # Simple priority ranking: top 3 absolute pct changes
    top_metrics = sorted(changes.items(), key=lambda kv: abs(kv[1]["pct_change"]), reverse=True)[:3]
    recommendations = [
        f"Investigate {m}" for m, _ in top_metrics
    ]

    # Build metrics table markdown
    rows = ["| Metric | Previous | Current | % Change |", "|---|---|---|---|"]
    for metric, info in changes.items():
        rows.append(f"| {metric} | {info['prev']} | {info['curr']} | {info['pct_change']}% |")
    metrics_table = "\n".join(rows)

    brief = ExecutiveBrief(
        date=datetime.date.today().isoformat(),
        headline="Executive KPI Summary",
        insights=insights,
        correlated_events=events,
        recommendations=recommendations,
        metrics_table=metrics_table,
    )
    print(brief.format())

if __name__ == "__main__":
    main()
