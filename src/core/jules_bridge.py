"""
Jules AI Bridge: Autonomous Task Dispatcher.
Routes structured architectural tasks to the Jules AI API,
which will execute them using its connected MCPs (v0, Linear, Neon, Render, etc).
"""
import os
import logging
import asyncio
import aiohttp
from dotenv import load_dotenv

from src.core.github_bridge import RepoManager

load_dotenv()

logger = logging.getLogger(__name__)

# v1alpha session states that mean the session has reached a final outcome.
_TERMINAL_STATES = {"COMPLETED", "FAILED", "CANCELLED"}


class JulesAIClient:
    """
    Asynchronous bridge to the Jules AI Agent API.
    Dispatches micro-tasks with MCP-aware prompting.
    """

    # MCP Routing Table: maps task types to Jules MCP instructions
    MCP_DIRECTIVES = {
        "ui":           "Use the v0 MCP to generate the spatial holographic UI components.",
        "database":     "Use the Neon MCP to provision and manage the serverless PostgreSQL instance.",
        "deployment":   "Use the Render MCP to deploy the service and monitor build logs.",
        "tracking":     "Use the Linear MCP to create tickets, break this into sub-issues, and track progress.",
        "docs":         "Use the Context7 MCP to pull the latest documentation for all referenced libraries.",
        "general":      "Execute this task using the best available MCP tools at your disposal."
    }

    def __init__(self):
        self.api_key = os.getenv("JULES_API_KEY", "")
        # Default to the real Jules endpoint; override via JULES_WEBHOOK_URL when needed.
        self.endpoint = os.getenv(
            "JULES_WEBHOOK_URL",
            "https://jules.googleapis.com/v1alpha/sessions",
        )
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    async def dispatch_task(
        self,
        task_type: str,
        architecture_plan: str,
        context: str = "",
        repo: str = "Moeabdelaziz007/AlphaEdge"
    ) -> dict:
        """
        Dispatches a structured task to the Jules AI API.
        
        Args:
            task_type: One of 'ui', 'database', 'deployment', 'tracking', 'docs', 'general'
            architecture_plan: The detailed plan Gemini/Groq produced.
            context: Optional extra context (e.g., build logs, error traces).
            repo: GitHub repo slug for Jules to operate on.
        
        Returns:
            Dict with 'success', 'message', and optionally 'task_id'.
        """
        mcp_instruction = self.MCP_DIRECTIVES.get(task_type, self.MCP_DIRECTIVES["general"])

        # Fetch live repo git state
        repo_mgr = RepoManager()
        git_status = repo_mgr.get_git_status()
        git_log = repo_mgr.get_git_log(count=3)

        payload = {
            "title": f"[AlphaEdge Auto-Dispatch] {task_type.upper()} Task",
            "instructions": (
                f"You are executing a task for the AlphaEdge project (repo: {repo}).\n\n"
                f"## MCP Directive\n{mcp_instruction}\n\n"
                f"## Architecture Plan\n{architecture_plan}\n\n"
                f"## Current Working Tree Status\n{git_status}\n\n"
                f"## Recent Local Commits\n{git_log}\n\n"
                f"## Additional Source Context\n{context or 'None provided.'}\n\n"
                "## Rules\n"
                "- Write production-quality code. Remember we run locally on macOS Metal.\n"
                "- Ensure compatibility with Three.js Holographic UI and existing Python meta_manager.\n"
                "- Push changes to a new branch and open a PR.\n"
                "- Do NOT duplicate code already shown in the context."
            ),
            "repository": repo,
            "trigger_source": "alpha_meta_loop"
        }

        if not self.api_key:
            return {
                "success": False,
                "message": "JULES_API_KEY not configured in .env",
                "payload_preview": payload
            }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.endpoint,
                    json=payload,
                    headers=self.headers,
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    if resp.status in (200, 201, 202):
                        data = await resp.json()
                        # v1alpha returns the full resource name (e.g.
                        # "sessions/12345"). Prefer that for downstream URL
                        # construction; fall back to "sessions/{id}" if only
                        # the bare id is present.
                        session_name = data.get("name")
                        if not session_name:
                            bare_id = data.get("id")
                            session_name = f"sessions/{bare_id}" if bare_id else None
                        return {
                            "success": True,
                            "message": f"Jules accepted task: {task_type}",
                            "task_id": session_name or "unknown",
                            "state": data.get("state", "QUEUED"),
                        }
                    else:
                        body = await resp.text()
                        return {
                            "success": False,
                            "message": f"Jules API returned {resp.status}: {body[:300]}"
                        }
        except asyncio.TimeoutError:
            return {"success": False, "message": "Jules API timed out (15s)."}
        except aiohttp.ClientError as e:
            return {"success": False, "message": f"Network error reaching Jules: {e}"}
        except Exception as e:
            # Graceful degradation: log the payload for manual dispatch
            return {
                "success": False,
                "message": f"Jules dispatch failed: {e}. Payload saved for manual review.",
                "payload_preview": payload
            }

    async def poll_status(self, task_id: str, max_attempts: int = 10, interval: float = 30.0) -> dict:
        """
        Polls the Jules v1alpha sessions API for task completion.

        `task_id` should be the full resource name returned by `dispatch_task`
        (e.g. "sessions/12345"). The v1alpha endpoint is
        `GET /v1alpha/sessions/{name}` with no `/status` suffix; completion is
        signalled via the `state` field (COMPLETED / FAILED / CANCELLED).

        Returns the final session resource on success, or a dict with
        `"state": "TIMEOUT"` / `"ERROR"` and an `error` message otherwise.
        """
        # Derive the sessions collection base URL from self.endpoint.
        # `endpoint` is typically `https://jules.googleapis.com/v1alpha/sessions`;
        # if a caller overrode it to a different path we still want the
        # `sessions/{id}` segment appended cleanly.
        base = self.endpoint.rstrip("/")
        # `task_id` already starts with "sessions/" when produced by dispatch_task.
        # Strip a duplicate prefix if the base also ends in "/sessions".
        session_path = task_id.lstrip("/")
        if base.endswith("/sessions") and session_path.startswith("sessions/"):
            poll_url = f"{base[: -len('sessions')]}{session_path}"
        else:
            poll_url = f"{base}/{session_path}"

        last_error: str | None = None
        for attempt in range(max_attempts):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        poll_url,
                        headers=self.headers,
                        timeout=aiohttp.ClientTimeout(total=10),
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            state = data.get("state", "UNKNOWN")
                            if state in _TERMINAL_STATES:
                                return data
                            last_error = None
                        else:
                            body = await resp.text()
                            last_error = f"HTTP {resp.status}: {body[:200]}"
                            logger.warning(
                                "Jules poll non-200 (attempt %d/%d): %s",
                                attempt + 1, max_attempts, last_error,
                            )
            except asyncio.TimeoutError:
                last_error = "request timed out (10s)"
                logger.warning(
                    "Jules poll timeout (attempt %d/%d) for %s",
                    attempt + 1, max_attempts, poll_url,
                )
            except aiohttp.ClientError as exc:
                last_error = f"network error: {exc}"
                logger.warning(
                    "Jules poll network error (attempt %d/%d): %s",
                    attempt + 1, max_attempts, exc,
                )

            await asyncio.sleep(interval * (1 + attempt * 0.3))

        return {
            "state": "TIMEOUT",
            "message": f"Polling timed out after {max_attempts} attempts.",
            "last_error": last_error,
        }
