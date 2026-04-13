"""
GitHub & Local Repo Bridge: The Codebase Nervous System.
Provides live local file access, remote GitHub API, and semantic code search.
No heavy dependencies (PyGithub/GitPython avoided) — uses REST + os for zero-cost edge.
"""
import os
import glob
import base64
import hashlib
import json
import subprocess
import requests
from typing import List, Optional
from pathlib import Path

# Project Root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class RepoManager:
    """
    Dual-mode codebase access:
    - LOCAL: Direct filesystem reads (instant, offline)
    - REMOTE: GitHub REST API (for PR creation, remote file reads, commit history)
    """

    SCAN_EXTENSIONS = {".py", ".js", ".css", ".html", ".md", ".toml", ".yml", ".yaml", ".json"}
    IGNORE_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv", ".egg-info",
                   "alphaedge.egg-info", "data", "models", ".idx", ".gemini"}

    def __init__(self):
        self.root = PROJECT_ROOT
        self.token = os.getenv("GITHUB_TOKEN", "")
        self.repo_slug = os.getenv("GITHUB_REPO", "Moeabdelaziz007/AlphaEdge")
        self.api_base = f"https://api.github.com/repos/{self.repo_slug}"
        self.headers = {"Accept": "application/vnd.github.v3+json"}
        if self.token and self.token != "your_github_token_here":
            self.headers["Authorization"] = f"Bearer {self.token}"

    # ═══════════════════════════════════════
    #  LOCAL FILE SYSTEM (Live Codebase DNA)
    # ═══════════════════════════════════════

    def get_local_file(self, filepath: str) -> str:
        """Read any file from the live local codebase."""
        full_path = os.path.join(self.root, filepath)
        if not os.path.exists(full_path):
            return f"[ERROR] File not found: {filepath}"
        try:
            with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            return content[:6000]  # Cap at 6k chars for context safety
        except Exception as e:
            return f"[ERROR] Reading {filepath}: {e}"

    def scan_codebase(self) -> List[dict]:
        """
        Walks the entire project tree and returns metadata for every source file.
        Returns: [{"path": "src/core/engine.py", "size": 1977, "hash": "abc123..."}]
        """
        results = []
        for root, dirs, files in os.walk(self.root):
            # Prune ignored directories
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS]

            rel_root = os.path.relpath(root, self.root)
            for fname in files:
                ext = os.path.splitext(fname)[1]
                if ext not in self.SCAN_EXTENSIONS:
                    continue

                rel_path = os.path.join(rel_root, fname) if rel_root != "." else fname
                full_path = os.path.join(root, fname)

                try:
                    stat = os.stat(full_path)
                    with open(full_path, 'rb') as f:
                        content_hash = hashlib.sha256(f.read()).hexdigest()

                    results.append({
                        "path": rel_path,
                        "size": stat.st_size,
                        "hash": content_hash,
                        "mtime": stat.st_mtime
                    })
                except Exception:
                    continue
        return results

    def get_file_tree(self, path: str = "") -> str:
        """Returns a formatted directory tree of the local codebase."""
        target = os.path.join(self.root, path) if path else self.root
        if not os.path.isdir(target):
            return f"Not a directory: {path}"

        lines = [f"📂 /{path or '(root)'}:"]
        try:
            for item in sorted(os.listdir(target)):
                if item in self.IGNORE_DIRS or item.startswith('.'):
                    continue
                full = os.path.join(target, item)
                icon = "📁" if os.path.isdir(full) else "📄"
                lines.append(f"  {icon} {item}")
        except Exception as e:
            lines.append(f"  Error: {e}")
        return "\n".join(lines)

    def search_local_files(self, query: str, max_results: int = 5) -> List[dict]:
        """
        Simple keyword search across local codebase files.
        Returns files containing the query string with context snippets.
        """
        results = []
        for root, dirs, files in os.walk(self.root):
            dirs[:] = [d for d in dirs if d not in self.IGNORE_DIRS]
            for fname in files:
                ext = os.path.splitext(fname)[1]
                if ext not in self.SCAN_EXTENSIONS:
                    continue

                full_path = os.path.join(root, fname)
                rel_path = os.path.relpath(full_path, self.root)

                try:
                    with open(full_path, 'r', encoding='utf-8', errors='replace') as f:
                        content = f.read()

                    if query.lower() in content.lower():
                        # Find the matching line for context
                        for i, line in enumerate(content.split('\n')):
                            if query.lower() in line.lower():
                                results.append({
                                    "path": rel_path,
                                    "line": i + 1,
                                    "snippet": line.strip()[:120]
                                })
                                break

                        if len(results) >= max_results:
                            return results
                except Exception:
                    continue
        return results

    def get_git_status(self) -> str:
        """Returns local git status."""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.root, capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                changes = result.stdout.strip()
                if not changes:
                    return "✅ Working tree clean."
                lines = changes.split('\n')
                return f"📝 {len(lines)} changed files:\n" + "\n".join(f"  {l}" for l in lines[:15])
            return f"Git error: {result.stderr[:200]}"
        except Exception as e:
            return f"Git unavailable: {e}"

    def get_git_log(self, count: int = 5) -> str:
        """Returns recent local git commits."""
        try:
            result = subprocess.run(
                ["git", "log", f"-{count}", "--oneline", "--no-decorate"],
                cwd=self.root, capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                return f"📝 Recent Commits:\n{result.stdout.strip()}"
            return f"Git log error: {result.stderr[:200]}"
        except Exception as e:
            return f"Git unavailable: {e}"

    # ═══════════════════════════════════════
    #  REMOTE GITHUB API
    # ═══════════════════════════════════════

    def _github_get(self, endpoint: str, params: dict = None) -> dict:
        try:
            resp = requests.get(
                f"{self.api_base}/{endpoint}",
                headers=self.headers, params=params or {}, timeout=10
            )
            if resp.status_code == 200:
                return {"ok": True, "data": resp.json()}
            return {"ok": False, "error": f"HTTP {resp.status_code}: {resp.text[:300]}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def get_repo_info(self) -> str:
        result = self._github_get("")
        if not result["ok"]:
            return f"GitHub Error: {result['error']}"
        d = result["data"]
        return (
            f"📦 {d['full_name']} ({d.get('visibility', 'unknown')})\n"
            f"⭐ Stars: {d.get('stargazers_count', 0)} | 🍴 Forks: {d.get('forks_count', 0)}\n"
            f"🐛 Open Issues: {d.get('open_issues_count', 0)}\n"
            f"🔧 Language: {d.get('language', 'N/A')}\n"
            f"📅 Last Push: {d.get('pushed_at', 'N/A')}"
        )

    def read_remote_file(self, path: str, branch: str = "main") -> str:
        result = self._github_get(f"contents/{path}", {"ref": branch})
        if not result["ok"]:
            return f"Remote file error: {result['error']}"
        data = result["data"]
        if data.get("encoding") == "base64":
            return base64.b64decode(data["content"]).decode("utf-8", errors="replace")[:4000]
        return "Cannot decode."

    def list_open_prs(self) -> str:
        result = self._github_get("pulls", {"state": "open", "per_page": 10})
        if not result["ok"]:
            return f"PR error: {result['error']}"
        prs = result["data"]
        if not prs:
            return "No open PRs."
        return "\n".join([f"  #{pr['number']} {pr['title']}" for pr in prs[:10]])

    def list_remote_commits(self, count: int = 5) -> str:
        result = self._github_get("commits", {"per_page": count})
        if not result["ok"]:
            return f"Commit fetch error: {result['error']}"
        if not result["data"]:
            return "No commits found."
        return "\n".join([f"  {c['sha'][:7]} - {c['commit']['message'].split(chr(10))[0][:80]}" for c in result["data"]])

    def merge_pr(self, pr_number: int) -> dict:
        """Merges a Pull Request via GitHub REST API (Squash Merge)."""
        try:
            resp = requests.put(
                f"{self.api_base}/pulls/{pr_number}/merge",
                headers=self.headers,
                json={"merge_method": "squash", "commit_title": f"Auto-Merge PR #{pr_number}"},
                timeout=15
            )
            if resp.status_code == 200:
                return {"ok": True, "message": f"Successfully merged PR #{pr_number}"}
            return {"ok": False, "error": f"Merge Error {resp.status_code}: {resp.json().get('message', resp.text)}"}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    # ═══════════════════════════════════════
    #  CODEBASE CONTEXT FOR JULES AI
    # ═══════════════════════════════════════

    def get_relevant_context(self, query: str, max_files: int = 3) -> str:
        """
        Finds the most relevant local files for a given query
        and returns their contents concatenated — ready to inject into Jules payload.
        """
        matches = self.search_local_files(query, max_results=max_files)
        if not matches:
            return "No relevant files found."

        context_parts = []
        for m in matches:
            content = self.get_local_file(m["path"])
            context_parts.append(f"### FILE: {m['path']} (match at line {m['line']})\n{content[:2000]}")

        return "\n\n".join(context_parts)
