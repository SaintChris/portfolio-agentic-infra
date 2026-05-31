# OWL Routing Rules — Task Delegation Protocol
# Updated: 2026-05-30
#
# When a user message arrives, OWL MUST classify and route it.
# Only handle directly: system commands (start/stop/status), config changes, secrets.

## Classification Rules

### Route to Market (inbox: ~/.shared/handoffs/inbox/Market/)
- Trading analysis, NQ/MNQ setups, market structure
- Economic data, Fed decisions, CPI, NFP
- Technical analysis, liquidity sweeps, order flow
- Keywords: trade, market, NQ, MNQ, liquidity, setup, level, fed, economic

### Route to Content (inbox: ~/.shared/handoffs/inbox/Content/)
- LinkedIn posts, articles, threads
- Professional portfolio, showcase website
- Content calendar, social media
- Keywords: linkedin, post, article, content, write, draft, social, portfolio

### Route to FE (inbox: ~/.shared/handoffs/inbox/FE/)
- Infrastructure setup, new tools, MCP servers
- Code, scripts, automation, CI/CD
- System architecture, new deployments
- Keywords: setup, deploy, code, script, build, infrastructure, tool, server

### Route to Finance Agent (inbox: ~/.shared/handoffs/inbox/Finance Agent/)
- Bank statements, P&L, financial reports
- Budget, expenses, income analysis
- Trading P&L, tax, ledger
- Keywords: finance, bank, statement, P&L, budget, expense, income, tax, ledger

### Route to IT Operations (inbox: ~/.shared/handoffs/inbox/IT Operations/)
- System health, cron jobs, error diagnosis
- Debugging, troubleshooting, monitoring
- Keywords: health, cron, error, debug, fix, down, broken, monitoring

### Route to CEO (inbox: ~/.shared/handoffs/inbox/CEO/)
- Strategy, coordination, multi-agent tasks
- Hiring/firing, prioritization
- Ambiguous messages that don't fit above categories
- Keywords: strategy, priority, team, coordinate, plan

## What OWL Handles Directly
- System status queries ("is X running?")
- Configuration changes to Hermes/Paperclip
- Secrets and API keys
- Direct file reads for quick lookups
- Responses to agent completion notes (DONE_ files)

## Routing Format
Create handoff file: ~/.shared/handoffs/inbox/{AGENT}/TO_{AGENT}_{YYYYMMDD}_{task}.md

```markdown
# {Task Title}

**From:** Alex (via OWL)
**Priority:** High | Medium | Low
**Date:** {YYYY-MM-DD}

## Task
{clear description of what needs to be done}

## Context
{any relevant context, file paths, background}

## Expected Output
{what the agent should produce}

## Deadline
{when it needs to be done, or "Next heartbeat"}
```
