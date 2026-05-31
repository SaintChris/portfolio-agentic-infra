#!/usr/bin/env python3
"""Paperclip Monitoring Dashboard Server
Serves dark-theme dashboard with live Paperclip stats + file browser + search.
"""

import json, os, re, subprocess, threading, time, sys
DEMO = "--demo" in sys.argv

from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler

API_BASE = "http://[HOST]:3100/api"
COMPANY_ID = "[COMPANY_ID]"
DASHBOARD_HTML = os.path.expanduser("~/Documents/Obsidian Vault/shared/projects/paperclip-dashboard/index.html")
HOME = os.path.expanduser("~")
ALLOWED_DIRS = [
    os.path.expanduser("~/Documents/Obsidian Vault"),
    os.path.expanduser("~/.shared"),
    os.path.expanduser("~/.hermes"),
    os.path.expanduser("~/Documents"),
    HOME,
]

_cache = {}
_cache_lock = threading.Lock()

def fetch_json(path):
    from urllib.request import urlopen, Request
    from urllib.error import URLError, HTTPError
    try:
        with urlopen(Request(f"{API_BASE}{path}", headers={"Accept":"application/json"}), timeout=5) as r:
            return json.loads(r.read())
    except:
        return None

def update_cache():
    while True:
        data = {}
        if DEMO:
            # Mock data for demo mode
            data["agents"] = [
                {"id": "a1", "name": "CEO", "status": "idle", "skillIds": ["strategic"]},
                {"id": "a2", "name": "Market Analyst", "status": "idle", "skillIds": ["analysis"]},
                {"id": "a3", "name": "Finance", "status": "idle", "skillIds": ["finance"]},
                {"id": "a4", "name": "Content Growth", "status": "idle", "skillIds": ["content"]},
                {"id": "a5", "name": "IT Ops", "status": "idle", "skillIds": ["ops"]},
                {"id": "a6", "name": "Founding Engineer", "status": "idle", "skillIds": ["infra"]},
            ]
            data["issues"] = [
                {"identifier": "ISS-1", "title": "Demo issue 1", "status": "todo"},
                {"identifier": "ISS-2", "title": "Demo issue 2", "status": "in_progress"},
            ]
            data["skillCount"] = 6
            data["heartbeats"] = [{"id": "run1", "agentId": "a2", "status": "running", "startedAt": time.time()}]
            data["infra"] = {"Gateway": "ok", "Paperclip": "ok", "Qdrant": "ok", "Ollama": "ok"}
        else:
            agents = fetch_json(f"/companies/{COMPANY_ID}/agents")
            if agents:
                data["agents"] = [a for a in agents if a.get("status") in ("idle","running")]
            issues = fetch_json(f"/companies/{COMPANY_ID}/issues")
            if issues:
                data["issues"] = [i for i in issues if i.get("status") not in ("done","cancelled","completed")]
            skills = set()
            for a in data.get("agents", []):
                for s in a.get("skillIds", []) or a.get("skills", []):
                    skills.add(str(s))
            data["skillCount"] = len(skills)
            runs = fetch_json(f"/companies/{COMPANY_ID}/runs?limit=20&order=desc")
            if runs:
                data["heartbeats"] = runs
            data["infra"] = check_infra()
        with _cache_lock:
            _cache.clear()
            _cache.update(data)
            _cache["timestamp"] = time.time()
        time.sleep(30)

def check_infra():
    """Check status of core services."""
    services = {
        "Gateway": ("[HOST]", 3100),  # Actually Paperclip — gateway doesn't have a port
        "Paperclip": ("[HOST]", 3100),
        "Qdrant": ("[HOST]", 6333),
        "Ollama": ("[HOST]", 11434),
    }
    # Also check gateway process
    result = {}
    # Check gateway by process
    gw = subprocess.run(["pgrep", "-f", "hermes.*gateway"], capture_output=True, text=True, timeout=3)
    result["Gateway"] = "ok" if gw.returncode == 0 else "err"
    # Check other services by port
    import socket
    for name, (host, port) in services.items():
        if name == "Gateway":
            continue
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(2)
            s.connect((host, port))
            s.close()
            result[name] = "ok"
        except:
            result[name] = "err"
    return result

def search_files(query, scope_dir, max_results=30):
    """Search file contents using rg or grep."""
    results = []
    # Find rg binary
    import shutil
    rg_path = shutil.which("rg") or "/opt/homebrew/bin/rg" or "/usr/bin/rg"
    try:
        # Use rg with --no-heading --line-number, plain text output (not --json)
        cmd = [rg_path, "--no-heading", "--line-number", "--max-count", "2",
               "--ignore-case", "--glob", "*.md", "--glob", "*.txt", "--glob", "*.json", "--glob", "*.yaml", "--glob", "*.yml",
               query, scope_dir]
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if proc.returncode == 0:
            for line in proc.stdout.strip().split("\n"):
                if not line: continue
                parts = line.split(":", 2)
                if len(parts) >= 3:
                    path = parts[0]
                    lineno = parts[1]
                    content = parts[2].strip()[:120]
                    # Highlight the match
                    content_lower = content.lower()
                    query_lower = query.lower()
                    idx = content_lower.find(query_lower)
                    if idx >= 0:
                        before = content[:idx]
                        match_text = content[idx:idx+len(query)]
                        after = content[idx+len(query):]
                        content = f"{before}§MATCH§{match_text}§/MATCH§{after}"
                    results.append({"path": path, "line": content, "lineno": lineno})
                    if len(results) >= max_results:
                        break
    except FileNotFoundError:
        try:
            cmd = ["grep", "-r", "-n", "-i", "--include=*.md", "--include=*.txt", query, scope_dir]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if proc.returncode == 0:
                for line in proc.stdout.strip().split("\n")[:max_results]:
                    if not line: continue
                    parts = line.split(":", 2)
                    if len(parts) >= 3:
                        results.append({"path": parts[0], "line": parts[2].strip()[:120], "lineno": parts[1]})
        except:
            pass
    except subprocess.TimeoutExpired:
        pass
    return results

class DashboardHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        path = self.path.split("?")[0]

        # Main dashboard HTML
        if path in ("/", "/index.html"):
            try:
                with open(DASHBOARD_HTML, "rb") as f:
                    html = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.send_header("Content-Length", str(len(html)))
                self.end_headers()
                self.wfile.write(html)
                return
            except FileNotFoundError:
                self.send_error(404, "Dashboard HTML not found")
                return

        # API stats endpoint (cached)
        if path == "/api/stats":
            with _cache_lock:
                data = dict(_cache)
            payload = json.dumps(data).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(payload)
            return

        # File browser: list local files
        if path == "/proxy/local-files":
            from urllib.parse import parse_qs
            qs = self.path.split("?", 1)[1] if "?" in self.path else ""
            params = parse_qs(qs)
            dirpath = params.get("dir", [""])[0]
            if dirpath and not any(os.path.realpath(dirpath).startswith(os.path.realpath(d)) for d in ALLOWED_DIRS if os.path.exists(dirpath)):
                if not any(dirpath.startswith(d) for d in ALLOWED_DIRS):
                    self.send_error(403, "Forbidden: path not in allowed dirs")
                    return
            try:
                entries = []
                for entry in sorted(os.listdir(dirpath)):
                    if entry.startswith("."): continue
                    full = os.path.join(dirpath, entry)
                    try:
                        s = os.stat(full)
                        entries.append({"name": entry, "isDir": os.path.isdir(full), "size": s.st_size if not os.path.isdir(full) else 0, "mtime": int(s.st_mtime)})
                    except OSError: pass
                payload = json.dumps(entries).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(payload)
            except Exception as e:
                self.send_error(500, str(e))
            return

        # File viewer
        if path == "/proxy/file":
            from urllib.parse import parse_qs
            qs = self.path.split("?", 1)[1] if "?" in self.path else ""
            params = parse_qs(qs)
            filepath = params.get("path", [""])[0]
            if not any(filepath.startswith(d) for d in ALLOWED_DIRS):
                self.send_error(403, "Forbidden")
                return
            try:
                with open(filepath, "rb") as f:
                    data = f.read()
                ct = "text/plain"
                ext = filepath.rsplit(".", 1)[-1].lower() if "." in filepath else ""
                cts = {"html": "text/html", "md": "text/markdown", "json": "application/json", "png": "image/png", "jpg": "image/jpeg", "gif": "image/gif", "pdf": "application/pdf"}
                ct = cts.get(ext, "text/plain")
                self.send_response(200)
                self.send_header("Content-Type", ct)
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
            except Exception as e:
                self.send_error(500, str(e))
            return

        # Content search
        if path == "/proxy/search":
            from urllib.parse import parse_qs
            qs = self.path.split("?", 1)[1] if "?" in self.path else ""
            params = parse_qs(qs)
            query = params.get("q", [""])[0]
            scope = params.get("scope", [HOME + "/Documents/Obsidian Vault"])[0]
            if not query:
                self.send_error(400, "Missing query")
                return
            results = search_files(query, scope)
            payload = json.dumps(results).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(payload)
            return

        # Regular Paperclip proxy
        if path.startswith("/proxy/"):
            api_path = self.path[len("/proxy"):]
            result = fetch_json(api_path)
            if result is not None:
                payload = json.dumps(result).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(payload)
            else:
                self.send_error(502, "Paperclip API unavailable")
            return

        self.send_error(404, "Not Found")

    def do_POST(self):
        path = self.path.split("?")[0]
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length else b""

        # Create local file
        if path == "/proxy/create-file":
            try:
                data = json.loads(body)
                filepath = data.get("path", "")
                content = data.get("content", "")
                if not any(filepath.startswith(d) for d in ALLOWED_DIRS):
                    self.send_error(403, "Forbidden: path not in allowed dirs")
                    return
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
                with open(filepath, "w") as f:
                    f.write(content)
                self.send_response(201)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True}).encode())
            except Exception as e:
                self.send_error(500, str(e))
            return

        self.send_error(404)

    def log_message(self, *a):
        pass

def run():
    server = ThreadingHTTPServer(("[HOST]", 9120), DashboardHandler)
    print("Dashboard: http://[HOST]:9120", flush=True)
    server.serve_forever()

if __name__ == "__main__":
    threading.Thread(target=update_cache, daemon=True).start()
    run()
