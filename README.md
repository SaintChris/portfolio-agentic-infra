# 🤖 Multi-Agent AI System

[![Live Demo](https://img.shields.io/badge/Live%20Demo-saintlex.sbs-blue)](https://saintlex.sbs/)
[![Tests](https://img.shields.io/badge/Tests%20Passing-52-success)](https://github.com/SaintChris/portfolio-agentic-infra)
[![Cost](https://img.shields.io/badge/Cost-%240%2Fmonth-success)](https://github.com/SaintChris/portfolio-agentic-infra)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE) [![Readers](https://img.shields.io/badge/Readers-0-blue)](https://github.com/SaintChris/portfolio-agentic-infra)

> 6 autonomous AI agents working in concert. Production delegation patterns. All running on free-tier models at **$0/month.**

---

## What This Is

A complete **multi-agent AI system** that automates a full business workflow using six specialized agents coordinating through a shared task queue.

**Key Highlights:**
- ✅ **Zero model cost** — All free-tier AI models and open-source tooling
- ✅ **Production-grade architecture** — Real delegation, testing, monitoring
- ✅ **Built for portfolio** — Targets Applied AI Engineer roles
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
- **Zero Cost** — All free-tier models, open-source tooling, **$0/month**
- **Demo Mode** — Run with mock data for instant demos (no backend dependencies)
- **52 Integration Tests** — Full test suite with rubric-based eval framework
- **Docker Ready** — One-command deployment with docker-compose

---

## 🧪 Testing

```bash
# Run all integration tests
python3 -m pytest tests/ -v

# Run eval framework
python3 tests/evals.py
```

✅ **52 assertions, all passing.**

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
├── examples/           # 5 production-grade agent implementations
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

Built to demonstrate **production-grade AI agent engineering skills:**

1. **Multi-agent orchestration** — Real delegation patterns, not just prompts
2. **Production architecture** — Tests, monitoring, containerization, documentation
3. **Cost engineering** — Designed from day one to run at zero model cost
4. **Real-world patterns** — Task queues, health checks, eval frameworks, human-in-the-loop

---

## 📄 License

MIT — Free to adapt and reuse.

---

## 👤 Author

**Alex Bogle** — AI Engineer based in Jamaica. Building production-grade AI agent infrastructure. 🔭 Open to Work — seeking Applied AI Engineer, ML Engineer, AI Solutions Engineer roles.

- 🌐 [saintlex.sbs](https://saintlex.sbs/)
- 💼 [linkedin.com/in/alex-bogle](https://linkedin.com/in/alex-bogle)
- 📧 [alex@alexbogle.com](mailto:alex@alexbogle.com)

---

> ⭐ If this project is useful or interesting, a star is appreciated — it helps others discover this work.
