#!/bin/bash
# IT Ops Health Check — Run on every heartbeat
# Checks: agent heartbeats, cron jobs, infrastructure

LOG_FILE="~/.hermes/logs/health-check.log"
mkdir -p "$(dirname "$LOG_FILE")"

check_time=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
echo "=== Health Check: $check_time ===" >> "$LOG_FILE"

ISSUES=0

# 1. Check all agents have heartbeat enabled
echo "[Agent Heartbeats]" >> "$LOG_FILE"
agent_json=$(curl -s http://[HOST]:3100/api/agents 2>/dev/null)
if [ -z "$agent_json" ]; then
  echo "  ❌ Paperclip API not responding" >> "$LOG_FILE"
  ISSUES=$((ISSUES + 1))
else
  echo "$agent_json" | python3 -c "
import json,sys
agents = json.loads(sys.stdin.read())
for a in agents:
    hb = a.get('runtimeConfig',{}).get('heartbeat',{})
    enabled = hb.get('enabled')
    interval = hb.get('intervalSec')
    last_hb = a.get('lastHeartbeatAt','never')
    name = a.get('name','?')
    if not enabled:
        print(f'  ❌ {name}: HEARTBEAT DISABLED')
    elif not last_hb or last_hb == 'never':
        print(f'  ⚠️  {name}: heartbeat enabled but never run (interval={interval}s)')
    else:
        print(f'  ✅ {name}: OK (last_hb={last_hb})')
" >> "$LOG_FILE"
fi

# 2. Check gateway
echo "[Infrastructure]" >> "$LOG_FILE"
if curl -s -o /dev/null http://[HOST]:9120/ 2>/dev/null; then
  echo "  ✅ Dashboard (:9120) OK" >> "$LOG_FILE"
else
  echo "  ❌ Dashboard (:9120) not responding" >> "$LOG_FILE"
  ISSUES=$((ISSUES + 1))
fi

if curl -s -o /dev/null http://[HOST]:3100/api/agents 2>/dev/null; then
  echo "  ✅ Paperclip (:3100) OK" >> "$LOG_FILE"
else
  echo "  ❌ Paperclip (:3100) not responding" >> "$LOG_FILE"
  ISSUES=$((ISSUES + 1))
fi

if pgrep -f "hermes_cli.main gateway" > /dev/null 2>&1; then
  echo "  ✅ Hermes gateway running" >> "$LOG_FILE"
else
  echo "  ❌ Hermes gateway not running" >> "$LOG_FILE"
  ISSUES=$((ISSUES + 1))
fi

# 3. Check disk
disk_usage=$(df / | tail -1 | awk '{print $5}' | tr -d '%')
if [ "$disk_usage" -gt 85 ]; then
  echo "  ⚠️  Disk usage: ${disk_usage}%" >> "$LOG_FILE"
  ISSUES=$((ISSUES + 1))
else
  echo "  ✅ Disk: ${disk_usage}%" >> "$LOG_FILE"
fi

# 4. Check load
load_1m=$(sysctl -n vm.loadavg | awk '{print $2}')
load_int=$(echo "$load_1m" | cut -d. -f1)
if [ "$load_int" -gt 5 ]; then
  echo "  ⚠️  Load: ${load_1m} (high for M1)" >> "$LOG_FILE"
else
  echo "  ✅ Load: ${load_1m}" >> "$LOG_FILE"
fi

# 5. Cron jobs
echo "[Cron Jobs]" >> "$LOG_FILE"
error_crons=$(python3 -c "
import json
with open('~/.hermes/cron/jobs.json') as f:
    data = json.load(f)
errors = [j for j in data['jobs'] if j.get('last_status') == 'error' and j.get('enabled')]
if errors:
    for j in errors:
        print(f'  ❌ {j[\"name\"]}: {j[\"last_status\"]}')
else:
    print('  ✅ No failing cron jobs')
" 2>/dev/null)
echo "$error_crons" >> "$LOG_FILE"

if echo "$error_crons" | grep -q "❌"; then
  ISSUES=$((ISSUES + 1))
fi

echo "[Result: $ISSUES issues]" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"

# Output issues for agent to act on
if [ "$ISSUES" -gt 0 ]; then
  echo "HEALTH_CHECK: $ISSUES issues detected"
  cat "$LOG_FILE" | tail -30
else
  echo "HEALTH_CHECK: All clear"
fi
