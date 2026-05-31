# System Overview – Portfolio Agentic Infra

## Introduction
This document provides a comprehensive architectural description of the **Portfolio Agentic Infrastructure** that powers the Paperclip AI platform, vector store, LLM embeddings, and monitoring dashboard. The goal is to deliver a production‑ready Docker Compose deployment that can be handed to employers for review, demonstrating competence in system design, scalability, security, and cost awareness.

---

## High‑Level Diagram (Textual)
```
[Client] → HTTP(S) → Dashboard (9120)
                               │
                               ▼
                         Paperclip API (3100)
                               │      ▲
                               │      │
          ┌────────────────────┼──────┘
          │                    │
          ▼                    ▼
   Qdrant Vector DB      PostgreSQL DB
   (6333)                (54329)
          │                    │
          ▼                    ▼
   Ollama Embedding LLM   Paperclip Workers
   (11434)                (internal)
```

## Components
| Component | Docker Image | Port | Role |
|-----------|--------------|------|------|
| **qdrant** | `qdrant/qdrant` | 6333 | Vector similarity store for embeddings. Persists data on a named volume `qdrant_storage`. |
| **ollama** | `ollama/ollama` | 11434 | Runs locally hosted LLMs that generate embeddings for Paperclip. Stores models in `ollama_models`. |
| **postgres** | `postgres:16` | 54329 (exposed) | Relational database backing Paperclip’s event store, user data, and configuration. Uses a dedicated volume `postgres_data`. |
| **paperclip** | `paperclipai/paperclip:latest` | 3100 | Core AI platform – orchestrates agents, runs prompts, stores artifacts. Depends on Postgres and optionally Qdrant. |
| **dashboard** | Build from `dashboard/` directory | 9120 | React/Next‑js UI for monitoring runs, viewing logs, and managing agents. |

## Data Flow
1. **User Request** – A request hits the dashboard (port 9120) via HTTPS.
2. **Dashboard → Paperclip** – The dashboard forwards the request to the Paperclip API (port 3100).
3. **Paperclip Execution** – Paperclip decides whether to store or retrieve vectors.
   * **Store** – Generates an embedding via Ollama (port 11434), then writes the embedding to Qdrant (port 6333).
   * **Retrieve** – Queries Qdrant for nearest neighbors, then resolves metadata from Postgres.
4. **Responses** travel back the same path to the dashboard and finally to the client.

## Scaling Considerations
- **Horizontal Scaling** – Each service can be replicated behind Docker Swarm or Kubernetes. Qdrant and Postgres support clustering; the docker‑compose file can be replaced with Helm charts for production.
- **Resource Isolation** – Services run on a dedicated bridge network `agentic-net` to avoid port collisions and to enable fine‑grained firewall rules.
- **Load‑Balancing** – When scaling, a reverse proxy (Traefik or NGINX) can distribute traffic among multiple Paperclip containers.

## Security Considerations
- **Secrets Management** – All secrets are injected via environment variables from the `.env` file. The file is excluded from version control (`.gitignore`). In production, use Docker secrets or a vault.
- **Network Segmentation** – Services not needing external exposure (Postgres, Qdrant, Ollama) are bound only to the internal Docker network.
- **Least Privilege** – PostgreSQL user `paperclip` has only the required database. Qdrant runs with default read/write permissions limited to its volume.
- **TLS** – Dashboard should be fronted by an external TLS termination proxy (e.g., Caddy) for HTTPS in production.

## Cost Analysis (Current – $0/month)
- **Local Docker** – No cloud provider costs; all services run locally on a development machine.
- **Future Cloud Deployment** – Estimated $10‑$20/month on a modest VPS (2 vCPU, 4 GB RAM, 50 GB SSD) covering all containers.
- **Optional Paid Services** – If Qdrant Cloud or a managed Postgres service is preferred, costs rise to ~$15/month each, still within a low‑budget regime.

## Deployment Instructions
1. Copy `.env.example` to `.env` and fill in real secret values.
2. Run `docker compose up -d` from the repository root.
3. Verify health checks: `docker compose ps` should show all services `healthy`.
4. Access the dashboard at `http://localhost:9120`.
5. Use the Paperclip CLI (`paperclip run …`) to interact with the API on `http://localhost:3100`.

---

## Appendix – Glossary
- **LLM** – Large Language Model, used here via Ollama.
- **Embedding** – Fixed‑size vector representation of text used for similarity search.
- **Vector DB** – Specialized database (Qdrant) for fast nearest‑neighbor queries.
- **Paperclip** – The orchestrator that runs autonomous agents, stores runs, and exposes an HTTP API.

*Document authored by the Founding Engineer on `$(date '+%Y-%m-%d')`.*
