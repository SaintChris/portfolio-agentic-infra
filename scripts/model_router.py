#!/usr/bin/env python3
"""
OWL Model Router — Intelligent free model selection for cron jobs.

Picks the best free model for each task based on:
1. Task complexity (quick check vs deep analysis vs report generation)
2. Provider rate limit status (tracks 429s per provider)
3. Freshness (prefers recently successful providers)
4. Load balancing (rotates across providers in same tier)

Usage:
  python3 model_router.py get <task_type>     # Get best model for task
  python3 model_router.py report <provider>   # Report a 429 from provider
  python3 model_router.py status              # Show current routing table
  python3 model_router.py refresh             # Fetch latest free models from OpenRouter
  python3 model_router.py test <task_type>    # Test a model selection

Task types:
  heartbeat   — Quick agent status checks (simple, frequent)
  health      — Infrastructure health checks (simple, daily)
  monitor     — Cross-agent outcome monitoring (medium complexity)
  security    — CEO dead man's switch (simple, must be reliable)
  research    — Job search, market research (medium, needs web)
  analysis    — Financial reports, market analysis (complex, large context)
  archive     — Session archiving (medium, needs context)
"""
import json, os, sys, time, random, datetime
from pathlib import Path

# --- Configuration ---
OPENROUTER_KEY_FILE = os.path.expanduser('~/.hermes/.env')
ROUTER_STATE_FILE = os.path.expanduser('~/.hermes/model_router_state.json')
FREE_MODELS_FILE = os.path.expanduser('~/.hermes/model_router_free_models.json')
OPENROUTER_API = 'https://openrouter.ai/api/v1'

# Task → capability requirements
TASK_PROFILES = {
    'heartbeat':  {'capability': 'small',  'min_ctx': 32000,  'priority': 'reliability', 'max_output': 500},
    'health':     {'capability': 'small',  'min_ctx': 32000,  'priority': 'reliability', 'max_output': 500},
    'security':   {'capability': 'medium', 'min_ctx': 100000, 'priority': 'reliability', 'max_output': 500},
    'monitor':    {'capability': 'medium', 'min_ctx': 100000, 'priority': 'balanced',    'max_output': 2000},
    'research':   {'capability': 'medium', 'min_ctx': 100000, 'priority': 'quality',      'max_output': 3000},
    'archive':    {'capability': 'medium', 'min_ctx': 100000, 'priority': 'balanced',    'max_output': 2000},
    'analysis':   {'capability': 'large',  'min_ctx': 250000, 'priority': 'quality',      'max_output': 5000},
    'briefing':   {'capability': 'large',  'min_ctx': 250000, 'priority': 'quality',      'max_output': 3000},
    'daily':      {'capability': 'medium', 'min_ctx': 100000, 'priority': 'balanced',    'max_output': 2000},
}

# Preferred models per task type (manually curated fallbacks)
TASK_FALLBACKS = {
    'heartbeat': ['openai/gpt-oss-120b:free', 'nvidia/nemotron-3-super-120b-a12b:free', 'minimax/minimax-m2.5:free'],
    'health':    ['minimax/minimax-m2.5:free', 'openai/gpt-oss-120b:free', 'nvidia/nemotron-3-super-120b-a12b:free'],
    'security':  ['deepseek/deepseek-v4-flash:free', 'nvidia/nemotron-3-super-120b-a12b:free', 'openai/gpt-oss-120b:free'],
    'monitor':   ['openai/gpt-oss-120b:free', 'nvidia/nemotron-3-super-120b-a12b:free', 'deepseek/deepseek-v4-flash:free'],
    'research':  ['openai/gpt-oss-120b:free', 'nvidia/nemotron-3-super-120b-a12b:free', 'minimax/minimax-m2.5:free'],
    'archive':   ['nvidia/nemotron-3-super-120b-a12b:free', 'openai/gpt-oss-120b:free', 'minimax/minimax-m2.5:free'],
    'analysis':  ['deepseek/deepseek-v4-flash:free', 'nvidia/nemotron-3-super-120b-a12b:free', 'qwen/qwen3-coder:free'],
    'briefing':  ['deepseek/deepseek-v4-flash:free', 'nvidia/nemotron-3-super-120b-a12b:free', 'qwen/qwen3-next-80b-a3b-instruct:free'],
    'daily':     ['openai/gpt-oss-120b:free', 'minimax/minimax-m2.5:free', 'nvidia/nemotron-3-super-120b-a12b:free'],
}


def load_key():
    """Load OpenRouter API key from env file."""
    try:
        with open(OPENROUTER_KEY_FILE) as f:
            for line in f:
                if line.strip().startswith('OPENROUTER_API_KEY'):
                    return line.strip().split('=', 1)[1].strip().strip('"')
    except:
        pass
    return None


def load_state():
    """Load router state (provider cooldowns, success counts)."""
    if os.path.exists(ROUTER_STATE_FILE):
        with open(ROUTER_STATE_FILE) as f:
            return json.load(f)
    return {'providers': {}, 'model_usage': {}, 'last_refresh': None}


def save_state(state):
    """Save router state."""
    os.makedirs(os.path.dirname(ROUTER_STATE_FILE), exist_ok=True)
    with open(ROUTER_STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def load_free_models():
    """Load cached free models data."""
    if os.path.exists(FREE_MODELS_FILE):
        with open(FREE_MODELS_FILE) as f:
            return json.load(f)
    return None


def refresh_free_models():
    """Fetch latest free models from OpenRouter API."""
    import requests
    
    key = load_key()
    if not key:
        print("ERROR: No OpenRouter key found")
        return None
    
    resp = requests.get(f'{OPENROUTER_API}/models', headers={'Authorization': f'Bearer {key}'}, timeout=15)
    if resp.status_code != 200:
        print(f"ERROR: OpenRouter returned {resp.status_code}")
        return None
    
    models = resp.json().get('data', [])
    free = []
    for m in models:
        if ':free' not in m.get('id', ''):
            continue
        ctx = m.get('context_length', 0)
        provider = m['id'].split('/')[0] if '/' in m['id'] else 'unknown'
        
        if ctx >= 500000: cap = 'xlarge'
        elif ctx >= 250000: cap = 'large'
        elif ctx >= 100000: cap = 'medium'
        else: cap = 'small'
        
        free.append({
            'id': m['id'],
            'provider': provider,
            'ctx': ctx,
            'capability': cap,
        })
    
    # Sort by quality (provider diversity + context)
    # Prefer: newer/bigger models, different providers
    provider_quality = {
        'openai': 10, 'deepseek': 9, 'nvidia': 9, 'google': 8, 'meta-llama': 8,
        'qwen': 7, 'minimax': 7, 'moonshotai': 6, 'nousresearch': 6,
        'poolside': 5, 'z-ai': 5, 'liquid': 4, 'cognitivecomputations': 4,
    }
    
    for m in free:
        m['quality_score'] = provider_quality.get(m['provider'], 5) + (m['ctx'] / 100000)
    
    free.sort(key=lambda x: x['quality_score'], reverse=True)
    
    with open(FREE_MODELS_FILE, 'w') as f:
        json.dump(free, f, indent=2)
    
    state = load_state()
    state['last_refresh'] = datetime.datetime.now().isoformat()
    save_state(state)
    
    print(f"Refreshed {len(free)} free models from OpenRouter")
    return free


def report_rate_limit(provider):
    """Report a 429 rate limit for a provider."""
    state = load_state()
    now = time.time()
    
    if provider not in state['providers']:
        state['providers'][provider] = {'rate_limits': [], 'successes': 0}
    
    state['providers'][provider]['rate_limits'].append(now)
    
    # Keep only last 100 rate limit events
    state['providers'][provider]['rate_limits'] = \
        state['providers'][provider]['rate_limits'][-100:]
    
    save_state(state)
    print(f"Reported rate limit for {provider}. Cooldown: 5 minutes.")


def get_provider_cooldown(provider):
    """Check if provider is in cooldown (had 429 in last 5 minutes)."""
    state = load_state()
    if provider not in state['providers']:
        return 0
    
    now = time.time()
    rate_limits = state['providers'][provider].get('rate_limits', [])
    
    # Count rate limits in last 5 minutes
    recent_429s = sum(1 for t in rate_limits if now - t < 300)
    
    if recent_429s >= 3:
        # Heavy rate limiting — 10 min cooldown
        oldest_recent = max(t for t in rate_limits if now - t < 300)
        return max(0, 600 - (now - oldest_recent))
    elif recent_429s >= 1:
        # Light rate limiting — 3 min cooldown
        return max(0, 180 - (now - rate_limits[-1]))
    
    return 0


def probe_model(model_id: str, timeout: int = 10) -> bool:
    """Probe a model endpoint with a lightweight call to verify it's live.
    
    Sends a minimal chat completion request. Returns True if the endpoint
    responds successfully, False otherwise.
    """
    import requests
    
    key = load_key()
    if not key:
        return False
    
    try:
        parts = model_id.split('/')
        model_name = parts[1] if len(parts) > 1 else model_id
        
        resp = requests.post(
            f"{OPENROUTER_API}/chat/completions",
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model_id,
                "messages": [{"role": "user", "content": "ping"}],
                "max_tokens": 1,
                "temperature": 0,
            },
            timeout=timeout,
        )
        
        if resp.status_code == 200:
            return True
        
        # Log the failure reason for debugging
        err_msg = ""
        try:
            err_msg = resp.json().get('error', {}).get('message', '')[:100]
        except Exception:
            err_msg = resp.text[:100]
        
        print(f"Probe {model_id}: HTTP {resp.status_code} — {err_msg}", file=sys.stderr)
        return False
        
    except requests.Timeout:
        print(f"Probe {model_id}: TIMEOUT after {timeout}s", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Probe {model_id}: ERROR — {e}", file=sys.stderr)
        return False


def get_best_model(task_type, exclude_providers=None):
    """Get the best free model for a task type, respecting rate limits and load balancing."""
    models = load_free_models()
    if not models:
        models = refresh_free_models()
    if not models:
        return 'openai/gpt-oss-120b:free'  # Ultimate fallback
    
    exclude = set(exclude_providers or [])
    profile = TASK_PROFILES.get(task_type, TASK_PROFILES['daily'])
    min_ctx = profile['min_ctx']
    priority = profile['priority']
    
    # Filter by capability and context
    candidates = [m for m in models if m['ctx'] >= min_ctx]
    
    # Remove providers in cooldown
    available = []
    cooldowns = {}
    for m in candidates:
        provider = m['provider']
        if provider in exclude:
            continue
        cooldown = get_provider_cooldown(provider)
        if cooldown > 0:
            cooldowns[provider] = cooldown
            continue
        available.append(m)
    
    if not available:
        # All providers in cooldown — use fallback chain
        fallbacks = TASK_FALLBACKS.get(task_type, TASK_FALLBACKS['daily'])
        for fb in fallbacks:
            if probe_model(fb):
                return fb
        return fallbacks[0]  # Return first fallback even if probe fails
    
    # Score each candidate
    state = load_state()
    scored = []
    for m in available:
        score = m['quality_score']
        
        # Bonus for providers not recently used
        model_id = m['id']
        usage = state.get('model_usage', {}).get(model_id, 0)
        score -= usage * 0.5  # Prefer less-used models
        
        # Reliability bonus for heartbeat/security tasks
        if priority == 'reliability':
            if m['provider'] in ('openai', 'nvidia', 'deepseek'):
                score += 2
        
        # Quality bonus for analysis tasks
        if priority == 'quality':
            if m['capability'] in ('xlarge', 'large'):
                score += 3
        
        scored.append((score, m['id'], m['provider']))
    
    scored.sort(reverse=True)
    
    # Probe the top candidates in order — return the first one that's live
    MAX_PROBES = 3
    for i, (score, model_id, provider) in enumerate(scored):
        if i >= MAX_PROBES:
            break  # Don't waste time probing too many
        if probe_model(model_id):
            # Track usage
            if 'model_usage' not in state:
                state['model_usage'] = {}
            state['model_usage'][model_id] = state['model_usage'].get(model_id, 0) + 1
            save_state(state)
            
            # Report cooldowns if any
            if cooldowns:
                msg = ', '.join(f"{p}: {t:.0f}s" for p, t in cooldowns.items())
                print(f"Cooldowns: {msg}", file=sys.stderr)
            
            print(f"Selected {model_id} (score={score:.1f}, probed OK)", file=sys.stderr)
            return model_id
        else:
            print(f"Probe FAILED for {model_id}, trying next...", file=sys.stderr)
            # Temporarily cooldown this provider
            report_rate_limit(provider)
    
    # All probes failed — use the first fallback that responds
    fallbacks = TASK_FALLBACKS.get(task_type, TASK_FALLBACKS['daily'])
    for fb in fallbacks:
        if probe_model(fb):
            return fb
    
    # Absolute fallback
    return 'openai/gpt-oss-120b:free'


def show_status():
    """Show current routing table and provider status."""
    models = load_free_models()
    state = load_state()
    
    print("=" * 100)
    print("OWL MODEL ROUTER STATUS")
    print("=" * 100)
    
    # Provider cooldowns
    print("\nProvider Cooldowns:")
    now = time.time()
    for provider, data in sorted(state.get('providers', {}).items()):
        recent_429s = sum(1 for t in data.get('rate_limits', []) if now - t < 300)
        cooldown = get_provider_cooldown(provider)
        if cooldown > 0:
            print(f"  ⚠️  {provider:25} | {recent_429s} recent 429s | cooldown: {cooldown:.0f}s")
        else:
            print(f"  ✅ {provider:25} | ready")
    
    # Current model assignments
    print("\nCurrent Model Assignments (by task):")
    for task_type in TASK_PROFILES:
        model = get_best_model(task_type)
        provider = model.split('/')[0] if '/' in model else '?'
        profile = TASK_PROFILES[task_type]
        print(f"  {task_type:15} → {model:50} | cap={profile['capability']}")
    
    # Model usage
    print("\nModel Usage (last tracking period):")
    usage = state.get('model_usage', {})
    for model, count in sorted(usage.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"  {model:55} | {count} uses")
    
    # Available free models
    if models:
        print(f"\nFree models available: {len(models)}")
        print(f"Last refresh: {state.get('last_refresh', 'never')}")
    
    print("\n" + "=" * 100)


def test_model_selection(task_type='monitor'):
    """Test model selection for a task."""
    print(f"Testing model selection for task: {task_type}")
    print(f"Profile: {TASK_PROFILES.get(task_type, {})}")
    
    model = get_best_model(task_type)
    print(f"Selected: {model}")
    
    # Show top 5 alternatives
    models = load_free_models()
    if models:
        profile = TASK_PROFILES.get(task_type, TASK_PROFILES['daily'])
        candidates = [m for m in models if m['ctx'] >= profile['min_ctx']]
        print(f"\nTop alternatives ({len(candidates)} total):")
        for m in candidates[:5]:
            cooldown = get_provider_cooldown(m['provider'])
            cd_str = f" [cooldown: {cooldown:.0f}s]" if cooldown > 0 else ""
            print(f"  {m['id']:50} | score={m.get('quality_score',0):.1f} | ctx={m['ctx']//1000}K{cd_str}")


# --- CLI ---
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'get':
        task = sys.argv[2] if len(sys.argv) > 2 else 'daily'
        print(get_best_model(task))
    
    elif cmd == 'report':
        provider = sys.argv[2] if len(sys.argv) > 2 else 'unknown'
        report_rate_limit(provider)
    
    elif cmd == 'status':
        show_status()
    
    elif cmd == 'refresh':
        refresh_free_models()
    
    elif cmd == 'test':
        task = sys.argv[2] if len(sys.argv) > 2 else 'monitor'
        test_model_selection(task)
    
    else:
        print(f"Unknown command: {cmd}")
        print(__doc__)
        sys.exit(1)
