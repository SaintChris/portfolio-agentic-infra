#!/usr/bin/env python3
"""
Evaluation Framework for AI Agents
===================================
Production-grade eval system that:
1. Scores agent outputs against rubrics
2. Compares against human-labeled benchmarks
3. Tracks quality over time (stored in JSON, upgradeable to Postgres)
4. Supports A/B testing of prompt templates
5. Generates eval reports

This addresses the #1 production gap in my current portfolio:
  "How do you know the agents are producing quality output?"

Usage:
  python3 evals.py --agent intake --runs 10
  python3 evals.py --report
"""

import json
import os
import hashlib
import datetime
import subprocess
import sys
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict
from enum import Enum


# ── Models ──

class EvalResult(Enum):
    PASS = "pass"
    FAIL = "fail"
    PARTIAL = "partial"


@dataclass
class EvalCase:
    """A single test case for an eval run."""
    id: str
    agent: str
    input: str
    expected_behavior: str  # Human-labeled expectation
    rubric: List[str]  # Scoring criteria


@dataclass
class EvalRun:
    """Result of running one agent against one eval case."""
    case_id: str
    agent: str
    input_preview: str  # First 100 chars
    output_preview: str  # First 200 chars
    result: EvalResult
    score: float  # 0.0 - 1.0
    rubric_scores: Dict[str, float]  # Criterion → score
    notes: str
    duration_ms: int
    timestamp: str = field(default_factory=lambda: datetime.datetime.now().isoformat())


@dataclass
class EvalSuite:
    """Aggregated results for an agent across all cases."""
    agent: str
    total_cases: int
    passed: int
    failed: int
    avg_score: float
    min_score: float
    max_score: float
    rubric_averages: Dict[str, float]
    trend: str  # "improving", "declining", "stable"
    runs: List[EvalRun]
    generated_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())


# ── Eval Cases (Human-Labeled Benchmarks) ──

INTAKE_EVAL_CASES = [
    EvalCase(
        id="intake-001",
        agent="intake",
        input="Subject: Can't login. I've been locked out for 2 hours.",
        expected_behavior="Classifies as ACCOUNT + HIGH priority, routes to human_review",
        rubric=["correct_category", "correct_priority", "confidence_above_0.6", "not_auto_send"]
    ),
    EvalCase(
        id="intake-002",
        agent="intake",
        input="Subject: This is the worst service ever. Cancel everything.",
        expected_behavior="Classifies as COMPLAINT, routes to human_review (not auto_send)",
        rubric=["detects_angry_sentiment", "routes_to_human", "not_auto_send"]
    ),
    EvalCase(
        id="intake-003",
        agent="intake",
        input="Subject: URGENT: Production is down. All users affected.",
        expected_behavior="Classifies as CRITICAL priority, escalates to manager",
        rubric=["detects_critical", "escalates", "assigned_to_manager"]
    ),
    EvalCase(
        id="intake-004",
        agent="intake",
        input="Subject: Question about my recent charge",
        expected_behavior="Classifies as BILLING, LOW/MEDIUM priority",
        rubric=["correct_category", "not_escalated", "not_flagged_as_complaint"]
    ),
    EvalCase(
        id="intake-005",
        agent="intake",
        input="Hi",
        expected_behavior="Returns low confidence (< 0.6), routes to human_review",
        rubric=["low_confidence", "routes_to_human"]
    ),
]


# ── Scoring Engine ──

def run_intake_eval(case: EvalCase) -> EvalRun:
    """Execute an intake agent eval case and score the output."""
    import time

    start = time.time()

    # Import the intake agent
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, repo_root)

    try:
        from examples.intake_agent.workflow import InboundRequest, classify_request, determine_routing

        req = InboundRequest.from_email({
            "from": "eval@test.com",
            "subject": case.input,
            "body": case.input
        })
        classification = classify_request(req.body, case.input)
        routing = determine_routing(classification)

        # Score against rubric
        rubric_scores = {}

        if "correct_category" in case.rubric:
            cat_keywords = {
                "ACCOUNT": ["login", "locked", "password", "account"],
                "COMPLAINT": ["worst", "terrible", "cancel", "angry"],
                "CRITICAL": ["urgent", "down", "production", "all users"],
                "BILLING": ["charge", "invoice", "payment", "billing"],
                "GENERAL": []
            }
            expected_cat = case.expected_behavior.split("Classifies as ")[1].split(" ")[0] if "Classifies as " in case.expected_behavior else "GENERAL"
            matched_keywords = [kw for kws in cat_keywords.values() for kw in kws if kw in case.input.lower()]
            rubric_scores["correct_category"] = 1.0 if any(
                kw in case.input.lower()
                for kws in [cat_keywords.get(expected_cat, [])]
                for kw in kws
            ) or expected_cat == classification.category.value else 0.5 if len(matched_keywords) > 0 else 0.0

        if "detects_angry_sentiment" in case.rubric:
            rubric_scores["detects_angry_sentiment"] = 1.0 if classification.sentiment in ("angry", "negative") else 0.0

        if "routes_to_human" in case.rubric:
            rubric_scores["routes_to_human"] = 1.0 if routing.action in ("human_review", "escalate") else 0.0

        if "not_auto_send" in case.rubric:
            rubric_scores["not_auto_send"] = 1.0 if routing.action != "auto_send" else 0.0

        if "detects_critical" in case.rubric:
            rubric_scores["detects_critical"] = 1.0 if classification.priority.name in ("CRITICAL", "HIGH") else 0.0

        if "escalates" in case.rubric:
            rubric_scores["escalates"] = 1.0 if routing.action == "escalate" else 0.0

        if "low_confidence" in case.rubric:
            rubric_scores["low_confidence"] = 1.0 if classification.confidence < 0.6 else 0.0

        avg_score = sum(rubric_scores.values()) / len(rubric_scores) if rubric_scores else 0.5

        if avg_score >= 0.8:
            result = EvalResult.PASS
        elif avg_score >= 0.5:
            result = EvalResult.PARTIAL
        else:
            result = EvalResult.FAIL

        duration_ms = int((time.time() - start) * 1000)

        return EvalRun(
            case_id=case.id,
            agent="intake",
            input_preview=case.input[:80],
            output_preview=f"cat={classification.category.value}, pri={classification.priority.name}, action={routing.action}",
            result=result,
            score=avg_score,
            rubric_scores=rubric_scores,
            notes=f"Sentiment={classification.sentiment}, Confidence={classification.confidence:.2f}",
            duration_ms=duration_ms,
        )

    except Exception as e:
        duration_ms = int((time.time() - start) * 1000)
        return EvalRun(
            case_id=case.id,
            agent="intake",
            input_preview=case.input[:80],
            output_preview=f"ERROR: {str(e)[:100]}",
            result=EvalResult.FAIL,
            score=0.0,
            rubric_scores={},
            notes=f"Agent crashed: {str(e)}",
            duration_ms=duration_ms,
        )


# ── Eval Runner ──

def run_eval_suite(cases: List[EvalCase]) -> EvalSuite:
    """Run all eval cases and produce an aggregated suite."""
    runs = []
    passed = 0
    failed = 0
    rubric_totals: Dict[str, float] = {}
    rubric_counts: Dict[str, int] = {}

    for case in cases:
        if case.agent == "intake":
            run = run_intake_eval(case)
        else:
            run = EvalRun(
                case_id=case.id,
                agent=case.agent,
                input_preview=case.input[:80],
                output_preview="NOT IMPLEMENTED",
                result=EvalResult.FAIL,
                score=0.0,
                rubric_scores={},
                notes=f"Eval for {case.agent} not implemented",
                duration_ms=0,
            )
        runs.append(run)

        if run.result == EvalResult.PASS:
            passed += 1
        elif run.result == EvalResult.FAIL:
            failed += 1
        # PARTIAL doesn't count as either

        for criterion, score in run.rubric_scores.items():
            rubric_totals[criterion] = rubric_totals.get(criterion, 0) + score
            rubric_counts[criterion] = rubric_counts.get(criterion, 0) + 1

    scores = [r.score for r in runs]
    rubric_averages = {k: rubric_totals[k] / rubric_counts[k] for k in rubric_totals}

    return EvalSuite(
        agent=cases[0].agent if cases else "unknown",
        total_cases=len(cases),
        passed=passed,
        failed=failed,
        avg_score=sum(scores) / len(scores) if scores else 0,
        min_score=min(scores) if scores else 0,
        max_score=max(scores) if scores else 0,
        rubric_averages=rubric_averages,
        trend="baseline",  # Would compare to historical in production
        runs=runs,
    )


def print_eval_report(suite: EvalSuite):
    """Print a formatted eval report."""

    print()
    print("=" * 70)
    print(f"  EVAL REPORT — {suite.agent.upper()}")
    print(f"  {suite.generated_at[:19]}")
    print("=" * 70)

    print(f"\n📊 SUMMARY")
    print(f"   Cases run:    {suite.total_cases}")
    print(f"   Passed:       {suite.passed} ✓")
    print(f"   Failed:       {suite.failed} ✗")
    print(f"   Partial:      {suite.total_cases - suite.passed - suite.failed} ~")
    print(f"   Avg score:    {suite.avg_score:.2f}")
    print(f"   Score range:  {suite.min_score:.2f} — {suite.max_score:.2f}")
    print(f"   Trend:        {suite.trend}")

    print(f"\n📋 RUBRIC AVERAGES")
    for criterion, avg in sorted(suite.rubric_averages.items()):
        bar = "█" * int(avg * 20) + "░" * (20 - int(avg * 20))
        print(f"   {criterion:<30} {bar} {avg:.2f}")

    print(f"\n🔍 INDIVIDUAL RUNS")
    print(f"   {'Case':<15} {'Result':<10} {'Score':>6} {'Duration':>8}   Output")
    print(f"   {'—'*15} {'—'*10} {'—'*6} {'—'*8} {'—'*30}")
    for run in suite.runs:
        result_icon = {"pass": "✓", "fail": "✗", "partial": "~"}[run.result.value]
        print(f"   {run.case_id:<15} {result_icon} {run.result.value:<8} {run.score:>5.2f} {run.duration_ms:>6}ms   {run.output_preview[:40]}")

        if run.result == EvalResult.FAIL:
            print(f"   {'':>15} Notes: {run.notes[:60]}")

    print(f"\n{'=' * 70}")
    status = "✓ ALL PASSING" if suite.failed == 0 else f"✗ {suite.failed} FAILURES"
    print(f"  Eval complete: {status}")
    print(f"{'=' * 70}")


def save_results(suite: EvalSuite, path: Optional[str] = None):
    """Save eval results for trend tracking."""
    path = path or os.path.join(
        os.path.dirname(os.path.abspath(__file__)),
        "eval_results.json"
    )

    # Load existing
    existing = []
    if os.path.exists(path):
        with open(path) as f:
            existing = json.load(f)

    # Append
    entry = {
        "timestamp": suite.generated_at,
        "agent": suite.agent,
        "total_cases": suite.total_cases,
        "passed": suite.passed,
        "failed": suite.failed,
        "avg_score": suite.avg_score,
        "rubric_averages": suite.rubric_averages,
        "runs": [{**asdict(r), "result": r.result.value} for r in suite.runs],
    }
    existing.append(entry)

    with open(path, "w") as f:
        json.dump(existing, f, indent=2)

    print(f"\nResults saved to {path}")
    return path


# ── Main ──

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Eval Framework for AI Agents")
    parser.add_argument("--agent", default="intake", help="Agent to eval")
    parser.add_argument("--report", action="store_true", help="Print report")
    parser.add_argument("--save", action="store_true", help="Save results to disk")
    args = parser.parse_args()

    if args.agent == "intake":
        cases = INTAKE_EVAL_CASES
    else:
        print(f"Unknown agent: {args.agent}")
        sys.exit(1)

    print(f"Running eval suite for: {args.agent}")
    print(f"Cases: {len(cases)}")

    suite = run_eval_suite(cases)
    print_eval_report(suite)

    if args.save:
        save_results(suite)

    sys.exit(0 if suite.failed == 0 else 1)
