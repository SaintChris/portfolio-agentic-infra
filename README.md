# Multi-Agent AI System — Portfolio

> **6 autonomous AI agents working in concert. All running on free-tier models at $0/month.**
> Built as a production-grade portfolio piece for Applied AI Engineer roles.

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue?logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-teal?logo=fastapi)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?logo=docker)](https://docker.com)
[![Tests](https://img.shields.io/badge/Tests-52%20Passing-green)](./tests)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

## What This Is

A complete multi-agent AI system that automates a full business workflow. Six specialized agents — CEO, Market Analyst, Content Growth, Finance, Ops, and Research — coordinate through a shared task queue with production delegation patterns.

**Key point:** Every component uses free-tier AI models and open-source tooling. Zero model cost. This is not a demo — it's a production architecture.

## Quick Start

```bash
git clone https://github.com/SaintChris/portfolio-agentic-infra.git
cd portfolio-agentic-infra

python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Live mode (full backend)
python3 dashboard/app.py

# Demo mode (mock data, no backend needed)
python3 dashboard/app.py --demo
```

Open `http://localhost:8501` for the live dashboard.

## Architecture

```
┌─────────────┐     ┌──────────────────┐     ┌─────────────┐
│  CEO Agent  │────▶│  Task Queue       │◀────│  Research   │
│  (orchestr.)│     │  (delegation)     │     │  Agent      │
└─────────────┘     └──────────────────┘     └─────────────┘
                           │    │    │
              ┌────────────┘    │    └────────────┐
              ▼                 ▼                  ▼
     ┌──────────────┐  ┌──────────────┐  ┌──────────────┐
     │ Market       │  │ Content      │  │ Finance      │
     │ Analyst      │  │ Growth       │  │ Agent        │
     └──────────────┘  └──────────────┘  └──────────────┘
```

## Agents

| Agent | Role | Key Capability |
|-------|------|----------------|
| **CEO** | Orchestrator | Monitors system health, delegates tasks, resolves conflicts |
| **Market Analyst** | Analysis | Macro insights, market data, trend identification |
| **Content Growth** | Content | LinkedIn posts, blog content, outreach automation |
| **Finance** | Financial | P&L tracking, budget monitoring, KPI reporting |
| **Ops** | Infrastructure | Deployment, health checks, system monitoring |
| **Research** | Intelligence | External data gathering, specialized analysis |

## Features

- **Agent Delegation Bridge** — Seamless handoff between agents via shared task queue
- **Live Dashboard** — Real-time Streamlit UI showing agent status, task queue, system health
- **Zero Cost** — All free-tier models, open-source tooling, $0/month
- **Demo Mode** — Run with mock data for instant demos (no backend dependencies)
- **52 Integration Tests** — Full test suite with rubric-based eval framework
- **Docker Ready** — One-command deployment with docker-compose

## Tech Stack

| Layer | Technology |
|-------|------------|
| Language | Python 3.11+ |
| API | FastAPI |
| Dashboard | Streamlit |
| Orchestration | Paperclip |
| Vector DB | Qdrant |
| LLM Inference | Ollama (local) |
| Storage | PostgreSQL |
| Deployment | Docker |

## Testing

```bash
# Run all integration tests
python3 -m pytest tests/ -v

# Run eval framework
python3 tests/evals.py
```

**Results:** 52 assertions, all passing. Rubric-based scoring with human-in-the-loop review queue.

## Repository Structure

```
portfolio-agentic-infra/
├── dashboard/          # Streamlit UI — live monitoring + demo mode
├── docs/               # Architecture docs and diagrams
├── examples/           # 5 production-grade agent implementations
├── scripts/            # Utility and setup scripts
├── tests/              # Integration tests + eval framework
├── docker-compose.yml  # Full stack: Qdrant, Ollama, Postgres, Paperclip
├── requirements.txt
├── .env.example
├── CONTRIBUTING.md
└── LICENSE (MIT)
```

## Why This Exists

Built to demonstrate production-grade AI agent engineering skills:

1. **Multi-agent orchestration** — Not just prompts, but real delegation patterns
2. **Production architecture** — Tests, monitoring, containerization, documentation
3. **Cost engineering** — Designed from day one to run at zero model cost
4. **Real-world patterns** — Task queues, health checks, eval frameworks, human-in-the-loop

## License

MIT — Free to adapt and reuse.

---

**Author:** [Alex Bogle](https://saintlex.sbs) · [LinkedIn](https://linkedin.com/in/alex-bogle) · [GitHub](https://github.com/SaintChris)