#!/usr/bin/env python3
"""
Inbox-to-Issue Bridge
Scans agent inbox directories and creates Paperclip issues for any unprocessed tasks.
Run as a cron job every 5 minutes.

This is the primary mechanism for task delegation: instead of relying on agents
to read inbox files (they don't — they check the Paperclip issue board), this
bridge converts inbox files into issues that agents will actually see and process.
"""

import json
import hashlib
import os
import sys
import urllib.request
import urllib.error
from datetime import datetime, timezone

# Config
COMPANY_ID = "[COMPANY_ID]"
PAPERCLIP_BASE = "http://[HOST]:3100"
STATE_FILE = os.path.expanduser("~/.hermes/scripts/inbox_bridge_state.json")
INBOX_BASE = os.path.expanduser("~/.shared/handoffs/inbox")

# Inbox directory name -> Agent ID
AGENT_MAP = {
    "Market": "7a16393a-7b65-41a3-9e42-ef1eab23e4ab",
    "Content": "395e7616-86ca-4311-b820-c382ab5238c9",
    "FE": "ba29ecb9-6462-4fc6-a6e8-b3a00915587b",
    "IT Operations": "088b7750-6ecb-4b3b-8759-a3c9e02d8f5c",
    "Finance Agent": "fa6518f7-f73e-4633-9871-4186187f0744",
    "CEO": "0c94382b-b43e-4e2b-b361-cb8a0b8d615e",
}


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"seen": {}, "stats": {"created": 0, "skipped": 0, "errors": 0}}


def save_state(state):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def file_hash(path):
    with open(path, "rb") as f:
        return hashlib.md5(f.read()).hexdigest()


def create_issue(title, description, agent_id, labels=None):
    payload = json.dumps({
        "title": f"[INBOX] {title}",
        "description": description,
        "assigneeAgentId": agent_id,
        "status": "todo",
        "labels": labels or ["inbox", "auto-bridge"]
    }).encode()

    req = urllib.request.Request(
        f"{PAPERCLIP_BASE}/api/companies/{COMPANY_ID}/issues",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    try:
        resp = urllib.request.urlopen(req, timeout=15)
        result = json.loads(resp.read())
        return result.get("id") or result.get("data", {}).get("id")
    except Exception as e:
        print(f"  ERROR creating issue: {e}", file=sys.stderr)
        return None


def main():
    state = load_state()
    created = 0
    skipped = 0
    errors = 0

    for inbox_dir, agent_id in AGENT_MAP.items():
        inbox_path = os.path.join(INBOX_BASE, inbox_dir)
        if not os.path.isdir(inbox_path):
            continue

        for filename in os.listdir(inbox_path):
            if not filename.endswith(".md"):
                continue
            if filename.startswith("DONE_"):
                continue  # Skip completion notes

            filepath = os.path.join(inbox_path, filename)
            fhash = file_hash(filepath)
            file_key = f"{inbox_dir}:{filename}"

            # Skip if already processed and unchanged
            if file_key in state["seen"] and state["seen"][file_key]["hash"] == fhash:
                skipped += 1
                continue

            # Read file content
            with open(filepath) as f:
                content = f.read()

            # Extract title from first line
            lines = content.strip().split("\n")
            title = lines[0].lstrip("# ").strip() if lines else filename

            # Create issue
            issue_id = create_issue(
                title=title,
                description=f"**Source:** {inbox_dir} inbox file: {filename}\n\n{content}",
                agent_id=agent_id,
                labels=["inbox", "auto-bridge"]
            )

            if issue_id:
                created += 1
                print(f"  Created issue {issue_id[:12]} for {inbox_dir}: {title[:50]}")
                state["seen"][file_key] = {
                    "hash": fhash,
                    "issue_id": issue_id,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
            else:
                errors += 1

    # Update stats
    state["stats"]["created"] += created
    state["stats"]["skipped"] += skipped
    state["stats"]["errors"] += errors
    state["stats"]["last_run"] = datetime.now(timezone.utc).isoformat()
    save_state(state)

    print(f"Bridge complete: {created} created, {skipped} skipped, {errors} errors")

    # Output for cron monitoring
    if created > 0:
        print(f"ALERT: {created} new tasks delegated to agents")


if __name__ == "__main__":
    main()
