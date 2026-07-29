# 🤖 Multi-Agent AI System

[![Live Demo](https://img.shields.io/badge/Live%20Demo-saintlex.sbs-blue)](https://saintlex.sbs/)
[![CI](https://github.com/SaintChris/portfolio-agentic-infra/actions/workflows/ci.yml/badge.svg)](https://github.com/SaintChris/portfolio-agentic-infra/actions)

[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE) [![Readers](https://img.shields.io/badge/Readers-0-blue)](https://github.com/SaintChris/portfolio-agentic-infra)

> Portfolio lab exploring six agent roles, a shared task queue, and a Streamlit dashboard. This is a learning project, not a production deployment.

---

## What This Is

A portfolio experiment that models six specialized agent roles coordinating through a shared task queue.

**Key Highlights:**
- **Local-first experiment** — Designed around local and free-tier tooling; actual operating cost depends on the selected providers and environment
- **Architecture experiment** — Delegation, tests, and monitoring concepts
- **Built for learning and demonstration** — Not enterprise production experience
- ✅ **Live dashboard** — Real-time monitoring via Streamlit

---

## 🚀 Quick Start

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

👉 Open `http://localhost:8501` for the live dashboard.

---

## 🏗️ Architecture

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

---

## 🤖 Agents

| Agent | Role | Key Capability |
|-------|------|----------------|
| **CEO** | Orchestrator | Monitors system health, delegates tasks, resolves conflicts |
| **Market Analyst** | Analysis | Macro insights, market data, trend identification |
| **Content Growth** | Content | LinkedIn posts, blog content, outreach automation |
| **Finance** | Financial | P&L tracking, budget monitoring, KPI reporting |
| **Ops** | Infrastructure | Deployment, health checks, system monitoring |
| **Research** | Intelligence | External data gathering, specialized analysis |

---

## ✨ Features

- **Agent Delegation Bridge** — Seamless handoff between agents via shared task queue
- **Live Dashboard** — Real-time Streamlit UI showing agent status, task queue, system health
- **Cost-conscious design** — Supports local and free-tier components; no universal monthly-cost claim is made
- **Demo Mode** — Run with mock data for instant demos (no backend dependencies)
- **Test suite included** — Current public CI is failing and must be repaired before any passing-test claim is made
- **Docker Ready** — One-command deployment with docker-compose

---

## 🧪 Testing

```bash
# Run all integration tests
python3 -m pytest tests/ -v

# Run eval framework
python3 tests/evals.py
```

The repository includes tests, but the current public GitHub Actions runs are failing. Run the suite in a clean environment and record the actual result before citing a passing count.

---

## 🛠️ Tech Stack

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

---

## 📁 Repository Structure

```
portfolio-agentic-infra/
├── dashboard/          # Streamlit UI — live monitoring + demo mode
├── docs/               # Architecture docs and diagrams
├── examples/           # Example agent workflow implementations
├── scripts/            # Utility and setup scripts
├── tests/              # Integration tests + eval framework
├── docker-compose.yml  # Full stack deployment
├── requirements.txt
├── .env.example
├── CONTRIBUTING.md
└── LICENSE (MIT)
```

---

## 💡 Why This Exists

Built to practice and demonstrate AI-agent engineering concepts:

1. **Multi-agent orchestration** — Real delegation patterns, not just prompts
2. **Architecture fundamentals** — Tests, monitoring, containerization, documentation
3. **Cost awareness** — Designed to support local and free-tier components where available
4. **Real-world patterns** — Task queues, health checks, eval frameworks, human-in-the-loop

---

## 📄 License

MIT — Free to adapt and reuse.

---

## 👤 Author

**Alex Bogle** — IT support and technical operations candidate based in Jamaica. This repository is a personal learning lab and is not presented as production employment experience.

- 🌐 [saintlex.sbs](https://saintlex.sbs/)
- 💼 [linkedin.com/in/alex-bogle](https://linkedin.com/in/alex-bogle)
- 📧 [alex@alexbogle.com](mailto:alex@alexbogle.com)

---

> ⭐ If this project is useful or interesting, a star is appreciated — it helps others discover this work.
