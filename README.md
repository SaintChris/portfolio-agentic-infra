# Portfolio Agentic Infrastructure

A collection of six AI agents that automate a complete workflow:
- **CEO** – orchestrates and monitors the system
- **Market Analyst** – provides macro insights and market analysis
- **Content Growth** – creates LinkedIn posts, blogs, and outreach content
- **Finance** – tracks P&L, budgets, and financial KPIs
- **Ops** – manages infrastructure, deployments, and health checks
- **Research** – gathers external data and runs specialized analyses

## Quick Start
```bash
# Clone the repo
git clone https://github.com/youruser/portfolio-agentic-infra.git
cd portfolio-agentic-infra

# Install dependencies (Python 3.11+ recommended)
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Run the dashboard (live mode)
python3 dashboard/app.py

# Or run in demo mode (mock data, no backend required)
python3 dashboard/app.py --demo
```

## Features
- **Agent Delegation Bridge**: Seamless handoff between agents via a shared task queue.
- **Live Dashboard**: Real‑time view of agent status, issue queue, and system health.
- **Zero Cost**: All components use free‑tier AI models and open‑source tooling.
- **Demo Mode**: Run the dashboard with mock data for quick demos.

## Built With
- Python 3.11
- FastAPI for the agent APIs
- Streamlit for the dashboard UI
- Docker for containerised deployment (optional)
- Paperclip for issue tracking and orchestration

## Contributing
Please see [`CONTRIBUTING.md`](CONTRIBUTING.md) for guidelines on how to propose changes, add new agents, and run tests.

## License
MIT License – feel free to adapt and reuse.
