"""
Jules AI Bridge: Autonomous Task Dispatcher.
Routes structured architectural tasks to the Jules AI API,
which will execute them using its connected MCPs (v0, Linear, Neon, Render, etc).
"""
import os
import json
import asyncio
import aiohttp
import aiohttp
from typing import Optional
from dotenv import load_dotenv

from src.core.github_bridge import RepoManager

load_dotenv()


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
        self.endpoint = os.getenv("JULES_WEBHOOK_URL", "https://api.jules.ai/v1/trigger")
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
                        return {
                            "success": True,
                            "message": f"Jules accepted task: {task_type}",
                            "task_id": data.get("id", "unknown"),
                            "status": data.get("status", "queued")
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
        Polls the Jules API for task completion status.
        Uses exponential-ish backoff.
        """
        for attempt in range(max_attempts):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.endpoint}/{task_id}/status",
                        headers=self.headers,
                        timeout=aiohttp.ClientTimeout(total=10)
                    ) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            status = data.get("status", "unknown")
                            if status in ("completed", "failed", "cancelled"):
                                return data
            except Exception:
                pass
            await asyncio.sleep(interval * (1 + attempt * 0.3))

        return {"status": "timeout", "message": f"Polling timed out after {max_attempts} attempts."}
