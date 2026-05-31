# Agentic Infrastructure Portfolio

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen)](https://github.com/saint/portfolio-agentic-infra/actions)
[![Agents](https://img.shields.io/badge/agents-6-blue)](##)
[![Cost](https://img.shields.io/badge/cost-$0%2Fmonth-success)](##)

## Quick Start
```bash
# Clone the repo
git clone https://github.com/saint/portfolio-agentic-infra.git
cd portfolio-agentic-infra
# Start services (Docker required)
docker-compose up -d
# Install Python deps
pip install -r requirements.txt
# Run dashboard (demo mode)
python3 dashboard/app.py --demo
```

---

**By Alex Bogle** — System built on Hermes Agent, Paperclip AI, Qdrant, and Ollama. Running on MacBook Air M1, 16GB RAM.

This repo showcases a production-grade multi-agent system I designed, built, and operate daily. Not a demo — a living infrastructure running real jobs, processing real data, and making real decisions.

---

## What This System Does

6 autonomous AI agents work in parallel on different domains, coordinated through a central task routing system:

| Agent | Role | Cadence | Model |
|-------|------|---------|-------|
| **CEO** | Orchestration, strategic decisions, delegation | 15 min | GPT-OSS-120B (free) |
| **Founding Engineer** | Infrastructure, DevOps, system maintenance | 20 min | GPT-OSS-120B (free) |
| **Market Analyst** | Trading analysis, market structure, level identification | 30 min | GPT-OSS-120B (free) |
| **Content & Growth** | LinkedIn strategy, content drafting, personal brand | 30 min | GPT-OSS-120B (free) |
| **IT Operations** | Security audits, system monitoring, routine maintenance | 30 min | GPT-OSS-120B (free) |
| **Finance Agent** | Expense tracking, financial reports, bank analysis | 30 min | GPT-OSS-120B (free) |

All agents use **free models exclusively** — OpenRouter, Groq, DeepInfra, Fireworks. **$0/month LLM cost.**

---

## Architecture

### Delegation Loop

```
User Request (Telegram DM)
    │
    ▼
┌──────────┐    ┌─────────────┐    ┌───────────────┐
│ OWL/Hermes│───▶│ ROUTING_RULES│───▶│ Task Classify │
│ (Gateway) │    │   .md       │    │ & Delegate    │
└──────────┘    └─────────────┘    └───────┬───────┘
                                           │
                    ┌──────────────────────┼──────────────────────┐
                    ▼                      ▼                      ▼
             CEO Orchestrator       Market Analyst          Finance Agent
             (strategic)            (trading intel)         (reports)
                    │                      │                      │
                    └──────────────────────┼──────────────────────┘
                                           ▼
                                   ┌───────────────┐
                                   │ Paperclip     │
                                   │ Issue Board   │
                                   │ (Postgres)    │
                                   └───────┬───────┘
                                           │ Inbox Bridge (every 5 min)
                                           ▼
                                   ┌───────────────┐
                                   │ Agent         │
                                   │ Heartbeats    │
                                   │ (5-30 min)    │
                                   └───────┬───────┘
                                           │
                                           ▼
                                   ┌───────────────┐
                                   │ Obsidian Vault │
                                   │ (outputs/)    │
                                   │ + Qdrant RAG  │
                                   └───────────────┘
```

### Key Components

| Component | Tech | Purpose |
|-----------|------|---------|
| **Gateway** | Hermes Agent | Message routing, memory, Telegram interface |
| **Agent Platform** | Paperclip AI | Agent lifecycle, issue board, skill management, heartbeats |
| **RAG** | Qdrant + Ollama | Vector search across Obsidian vault, trading data, financial records |
| **Cron Scheduler** | Standalone Python | Job orchestration with file-lock dedup, independent of gateway |
| **Model Router** | Custom Python | Adaptive model selection across 23 free models, 13 providers |
| **Inbox Bridge** | Custom Python | Converts inbox tasks → Paperclip issues (delegation backbone) |
| **Dashboard** | Python + vanilla JS | Real-time monitoring: agents, infrastructure, file browser, search |
| **Knowledge Store** | Obsidian Vault | Daily logs, entity pages, working context, session archives |

---

## Built With

- **Hermes Agent** – Telegram interface, memory, session search
- **Paperclip AI** – Issue board, heartbeats, skill routing
- **Qdrant** – Vector DB for RAG
- **Ollama** – Local embeddings and LLM inference
- **Docker Compose** – Service orchestration (Qdrant, Paperclip, Ollama)
- **Python 3.12** – Core logic, dashboards, scripts

---

## Key Engineering Decisions

### Why Paperclip + Hermes (not LangGraph / CrewAI)

- Paperclip handles agent state, heartbeats, skill management, and issue tracking out of the box — no custom scaffolding needed
- Hermes gives me Telegram-native messaging, persistent memory, session search, and cron scheduling
- Together, they cover the full lifecycle without building agents from scratch
- The "inbox-to-issue bridge" pattern solved the fundamental problem of getting autonomous agents to pick up tasks reliably

### Why Free Models Exclusively

- OpenRouter paid account gives unlimited rate limits on their free tier
- GPT-OSS-120B (OpenAI's open-weight model) runs at no cost via OpenRouter
- 6 agents × 30+ heartbeats/day = ~500+ API calls daily = **$0**
- The model router automatically fails over across 13 providers (OpenRouter, Groq, DeepInfra, Fireworks, etc.)

### Why Custom Cron Scheduler (not Hermes built-in cron)

- Gateway restarts kill in-memory cron state
- Standalone scheduler reads `jobs.json` directly, runs as a separate LaunchAgent
- File-lock prevents double-firing with gateway's internal cron
- Agent jobs use explicit model assignments (not inferred `-auto-` which causes 429s)

### Why Inbox-to-Issue Bridge

- Agents reliably check the Paperclip issue board every heartbeat (this is hardcoded in their session context)
- They do NOT reliably read inbox directories (agents ignored inbox files placed by other agents or crons)
- Bridge converts `.md` handoff files → Paperclip issues, MD5-deduped, every 5 minutes
- This is the delegation backbone — all task handoffs go through this

### Why Qdrant over Other Vector DBs

- Runs in a single OrbStack container (minimal resource footprint on 16GB RAM)
- 3 collections: vault knowledge (235 vectors), trading data (33 vectors), financial records (204 vectors)
- Ollama `nomic-embed-text` for 768-dim cosine similarity embeddings
- Used for RAG lookups during agent heartbeats and ad-hoc queries

---

## Repository Structure

```
├── README.md                    # This file
├── docs/
│   ├── ROUTING_RULES.md         # Task classification matrix (OWL → agent)
│   ├── architecture/
│   │   └── system-overview.md   # Detailed architecture doc
│   └── screenshots/             # Dashboard screenshots
├── dashboard/
│   ├── index.html               # Dark-theme monitoring dashboard
│   └── app.py                   # Dashboard server (Python)
├── scripts/
│   ├── inbox_bridge.py          # Inbox → Paperclip issue converter
│   ├── model_router.py          # Adaptive free-model router
│   └── health/
│       ├── health-check.sh      # System health verification
│       └── qdrant-check.sh      # Qdrant collection health
├── agents/
│   ├── ceo/RUNBOOK.md           # CEO agent runbook
│   ├── founding-engineer/RUNBOOK.md
│   ├── market-analyst/RUNBOOK.md
│   ├── content-growth/RUNBOOK.md
│   ├── it-ops/RUNBOOK.md
│   └── finance/RUNBOOK.md
├── config/
│   └── cron/jobs.json           # Cron job definitions (sanitized)
└── docker-compose.yml           # Qdrant, Paperclip stack
```

---

## Dashboard Features

- **Agent Status** — live heartbeat data, skill count, run history
- **Infrastructure** — gateway, Paperclip, Qdrant, Ollama health
- **File Browser** — navigate Vault, Shared workspace, Hermes config, agent outputs
- **Content Search** — full-text ripgrep search across all markdown/docs
- **Create Files** — create `.md`, `.txt`, `.json`, `.yaml`, `.py`, `.sh` from the browser
- **Task Board** — Paperclip issues sorted by creation date

---

## What I'd Build Next

If this were a production system for a client (not personal infrastructure):

1. **Auth layer** — JWT or session-based access to the dashboard
2. **Webhook endpoints** — external systems triggering agent workflows via HTTP
3. **Audit trail** — structured logging of all inter-agent task handoffs
4. **Evaluation loop** — automated quality scoring of agent outputs
5. **Human review queue** — flagged outputs requiring approval before publishing
6. **Client-facing agent** — external request intake → classify → route → respond pattern

---

## About Me

**Alex Bogle** — Hellshire, Portmore, Jamaica (ET)  
4+ years IT ops | Google IT Cert 2025 | Building toward trading independence  
Direct communication style. Ship first, polish later. Free/open-source everything.

**Looking for:** Remote roles in AI engineering, agentic systems, or IT operations.  
**Also available for:** Hermes Agent setup and deployment ($1,500-$5,000/client).
