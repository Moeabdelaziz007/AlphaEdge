import os
import json
import asyncio
import sqlite3
import datetime
from src.core.github_bridge import RepoManager
from src.core.jules_bridge import JulesAIClient

class ReflectionEngine:
    """The Analytical Brain: Distills lessons from past outcomes."""
    def __init__(self, db_path="data/db/memory.sqlite"):
        self.db_path = db_path

    def log_reflection(self, task_id: str, reflection: str, score: float):
        """Stores a self-critique entry."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "INSERT INTO reflection_logs (task_id, reflection, score) VALUES (?, ?, ?)",
                (task_id, reflection, score)
            )

    async def audit_prompts(self, ai_manager):
        """Analyzes recent logs to suggest prompt mutations if failure patterns (score < 0.5) exist."""
        with sqlite3.connect(self.db_path) as conn:
            # Find the most recent failures
            cursor = conn.execute("SELECT reflection FROM reflection_logs WHERE score < 0.5 ORDER BY timestamp DESC LIMIT 3")
            failures = cursor.fetchall()
            
            if failures:
                lessons = "\n".join([f"- {f[0]}" for f in failures])
                mutation_prompt = (
                    f"I have detected a pattern of failures in our system prompts. \n"
                    f"RECENT FAILURES:\n{lessons}\n\n"
                    "Analyze these and suggest a mutated (improved) version of the System Prompt listed below to prevent these errors.\n"
                    f"CURRENT PROMPT:\n{ai_manager.system_prompt}"
                )
                # This would be processed by Gemini for mutation
                return mutation_prompt
        return None

class CuriosityDaemon:
    """The Idle Learner: Scans the repo for refactoring opportunities."""
    def __init__(self, repo_manager: RepoManager):
        self.repo = repo_manager
        self.jules = JulesAIClient()

    async def hunt_for_improvements(self):
        """Scans the codebase and tasks Jules with optimizing a specific module."""
        # Pick a random or complex file
        files = self.repo.scan_codebase()
        if not files: return
        
        # Sort by size or just pick one
        target_file = files[0]["path"]
        content = self.repo.get_local_file(target_file)
        
        plan = (
            f"Analyze the file '{target_file}' for memory efficiency and latency. "
            "Identify one mathematical or logical improvement. "
            "Implement the change and push to a new branch 'auto-evolve/optimization-alpha'."
        )
        # Note: We don't push until approval usually, but the policy says:
        # "It must checkout a new isolated branch... It must generate a Pull Request"
        print(f"🧬 Curiosity Daemon focusing on: {target_file}")
        # In a real run, this calls self.jules.dispatch_task(...)
        return f"Suggested improvement for {target_file} dispatched to Jules."
