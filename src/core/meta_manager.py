"""
The Meta-Manager: AlphaEdge's Autonomous Observer Loop.
Listen -> Reflect (Groq) -> Skill-Make (Gemini) -> Execute -> Jules Dispatch -> Reflect & Remember.
Drives the WebSocket-powered Holographic UI and Self-Improving Memory.
"""
import os
import sys
import json
import asyncio
import subprocess
import shutil
import traceback
import time
from typing import Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))

from src.core.ai_client import AIClient
from src.skills import list_skills, load_skill, SKILLS_DIR
from src.core.jules_bridge import JulesAIClient
from src.core.github_bridge import RepoManager
import urllib.parse
import requests
import re
import google.generativeai as genai
from src.core.saas_manager import SaaSManager, SaaSProject
from src.core.telemetry import TelemetryLogger

# Codebase Nervous System
repo = RepoManager()

# Initialize AI Engines
ai_client = AIClient()
genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))
gemini_model = genai.GenerativeModel('gemini-1.5-flash')

# Jules Bridge Singleton
jules = JulesAIClient()

# Docker availability check (cached)
DOCKER_AVAILABLE = shutil.which("docker") is not None


class MetaManager:
    """
    The Autonomous Observer Loop.
    Listen -> Reflect -> [Skill-Make | Execute | Jules Dispatch] -> Speak -> Remember.
    """

    def __init__(self):
        self.state = "idle"
        self.ws_broadcast = None
        self.system_telemetry: list[dict] = []
        self.telemetry = TelemetryLogger(self.system_telemetry)
        self.conversation = [
            {"role": "system", "content": (
                "You are AlphaEdge's Meta-Manager, an autonomous 10x architect. "
                "You have these actions available:\n"
                "1. {\"action\": \"create_skill\", \"skill_name\": \"...\", \"description\": \"...\", \"python_code\": \"...\"} "
                "- When asked to do something you lack a tool for.\n"
                "2. {\"action\": \"execute_skill\", \"skill_name\": \"...\"} "
                "- When a matching skill already exists.\n"
                "3. {\"action\": \"dispatch_jules\", \"task_type\": \"ui|database|deployment|tracking|docs|general\", "
                "\"architecture_plan\": \"...\", \"context\": \"...\"} "
                "- For complex infrastructure tasks that need Jules AI + MCPs.\n"
                "4. {\"action\": \"analyze_code\", \"query\": \"...\", \"file_path\": \"...\"} "
                "- To search/read the live codebase. Use 'query' for keyword search or 'file_path' to read a specific file.\n"
                "5. {\"action\": \"search_web\", \"query\": \"...\"} "
                "- Search the internet for latest tech, open source tools, docs, or errors.\n"
                "6. {\"action\": \"analyze_chat_logs\", \"query\": \"...\"} "
                "- Read the Telegram chat history to analyze past conversations, errors, and debug.\n"
                "7. {\"action\": \"update_memory\", \"new_content\": \"...\"} "
                "- Rewrite the heartbeat.md file to mark tasks as completed or add new findings.\n"
                "8. {\"action\": \"speak\", \"text\": \"...\"} - For conversational responses.\n\n"
                "CRITICAL INSTRUCTIONS (ANTI-GRAVITY PROTOCOL):\n"
                "1. You are not a chatbot. You are AlphaEdge, a persistent, state-aware Senior Software Engineer and 10x Architect.\n"
                "2. You possess Agentic Permanence. Read your memory, observe the codebase, and act deliberately.\n"
                "3. You MUST ALWAYS speak and converse entirely in Arabic (اللغة العربية).\n"
                "4. When generating text/reports/reflections, output them in Arabic.\n\n"
                "ALWAYS respond with valid JSON. Nothing else. "
                "Context: AlphaEdge runs on Apple Metal GPU with llama.cpp.\n"
                "Strategic Awareness - Mitigate these 6 Weaknesses:\n"
                "1. Hardware dependency -> Expand hardware support\n"
                "2. Cognitive switching complexity -> Simplify protocol\n"
                "3. Scalability limits -> Invest in scalability research\n"
                "4. Privacy concerns -> Execute strict privacy measures\n"
                "5. Lack of commercialization -> Develop commercial strategy\n"
                "6. Reliance on 3rd party -> Diversify tech reliance"
            )}
        ]
        self.saas = SaaSManager(self)

    @staticmethod
    def _extract_tokens_used(response) -> Optional[int]:
        """Best-effort extraction of token usage across providers."""
        if response is None:
            return None
        usage = getattr(response, "usage", None)
        if usage is not None:
            return (
                getattr(usage, "total_tokens", None)
                or getattr(usage, "total_token_count", None)
                or getattr(usage, "prompt_tokens", 0) + getattr(usage, "completion_tokens", 0)
            )
        usage_meta = getattr(response, "usage_metadata", None)
        if usage_meta is not None:
            return (
                getattr(usage_meta, "total_token_count", None)
                or getattr(usage_meta, "prompt_token_count", 0) + getattr(usage_meta, "candidates_token_count", 0)
            )
        return None

    async def broadcast_state(self, state: str, data: dict = None):
        """Push real-time state updates to all connected WebSocket clients."""
        self.state = state
        payload = {"state": state}
        if data:
            payload.update(data)
        if self.ws_broadcast:
            await self.ws_broadcast(json.dumps(payload))

    # ─── Phase 1: Reflect (Groq Intent Parser) ───
    async def reflect(self, user_text: str) -> dict:
        await self.broadcast_state("reflecting", {"label": "Groq Parsing Intent..."})
        started = time.perf_counter()
        ram_before = self.telemetry.current_rss()
        success = False
        tokens_used = None
        error = None

        available = list_skills()
        skill_context = f"Available skills: {available}" if available else "No skills learned yet."

        self.conversation.append({
            "role": "user",
            "content": f"[SKILL_REGISTRY]: {skill_context}\n\n[USER_QUERY]: {user_text}"
        })

        try:
            response = ai_client.chat_completion(
                messages=self.conversation,
                max_tokens=2048,
                response_format={"type": "json_object"}
            )
            tokens_used = self._extract_tokens_used(response)
            raw = response.choices[0].message.content
            self.conversation.append({"role": "assistant", "content": raw})
            success = True
            return json.loads(raw)
        except Exception as e:
            error = str(e)
            return {"action": "speak", "text": f"Reflection error: {e}"}
        finally:
            self.telemetry.log_action(
                action="reflect",
                agent="groq",
                success=success,
                duration_ms=(time.perf_counter() - started) * 1000,
                ram_before=ram_before,
                ram_after=self.telemetry.current_rss(),
                tokens_used=tokens_used,
                error=error,
            )

    # ─── Phase 2: Skill-Maker (Gemini Deep Brain + Docker Sandbox) ───
    async def build_skill(self, skill_name: str, description: str, python_code: str) -> str:
        await self.broadcast_state("skill_building", {"label": f"Forging Skill: {skill_name}"})
        started = time.perf_counter()
        ram_before = self.telemetry.current_rss()
        success = False
        tokens_used = None
        error = None

        try:
            skill_path = os.path.join(SKILLS_DIR, f"{skill_name}.py")

            # Enrich the code with Gemini
            try:
                gemini_prompt = (
                    f"Review and improve this Python skill script. "
                    f"It must have a `run()` function that returns a string result. "
                    f"Fix any bugs. Output ONLY the improved Python code, no markdown.\n\n"
                    f"Description: {description}\n\nCode:\n{python_code}"
                )
                gemini_response = gemini_model.generate_content(gemini_prompt)
                tokens_used = self._extract_tokens_used(gemini_response)
                improved_code = gemini_response.text.replace("```python", "").replace("```", "").strip()
            except Exception:
                improved_code = python_code

            # Write the skill file
            with open(skill_path, 'w') as f:
                f.write(improved_code)

            # Test in Docker Sandbox (preferred) or subprocess fallback
            await self.broadcast_state("skill_building", {"label": f"Sandbox Testing: {skill_name}"})
            test_result = await self._sandbox_test(skill_path, skill_name)

            if not test_result["success"]:
                if os.path.exists(skill_path):
                    os.remove(skill_path)
                error = test_result["error"]
                return f"❌ Skill '{skill_name}' failed: {test_result['error']}"

            success = True
            return f"✅ Skill '{skill_name}' forged and registered! Output: {test_result['output'][:300]}"
        finally:
            self.telemetry.log_action(
                action="build_skill",
                agent="gemini",
                success=success,
                duration_ms=(time.perf_counter() - started) * 1000,
                ram_before=ram_before,
                ram_after=self.telemetry.current_rss(),
                tokens_used=tokens_used,
                error=error,
            )

    async def _sandbox_test(self, skill_path: str, skill_name: str) -> dict:
        """Tests a skill in Docker (if available) or subprocess fallback."""
        test_cmd = (
            f"import importlib.util; "
            f"spec = importlib.util.spec_from_file_location('s', '{skill_path}'); "
            f"m = importlib.util.module_from_spec(spec); "
            f"spec.loader.exec_module(m); print(m.run())"
        )

        if DOCKER_AVAILABLE:
            try:
                result = subprocess.run(
                    ["docker", "run", "--rm", "-v", f"{skill_path}:/skill.py:ro",
                     "python:3.11-slim", "python", "-c",
                     "import importlib.util; spec = importlib.util.spec_from_file_location('s', '/skill.py'); m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); print(m.run())"],
                    capture_output=True, text=True, timeout=30
                )
                if result.returncode == 0:
                    return {"success": True, "output": result.stdout}
                return {"success": False, "error": result.stderr[:500]}
            except Exception as e:
                # Docker failed, fall through to subprocess
                pass

        # Subprocess fallback
        try:
            result = subprocess.run(
                [sys.executable, "-c", test_cmd],
                capture_output=True, text=True, timeout=15
            )
            if result.returncode == 0:
                return {"success": True, "output": result.stdout}
            return {"success": False, "error": result.stderr[:500]}
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Timed out (15s)"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ─── Phase 3: Execute Existing Skill ───
    async def execute_skill(self, skill_name: str) -> str:
        await self.broadcast_state("executing", {"label": f"Running: {skill_name}"})
        started = time.perf_counter()
        ram_before = self.telemetry.current_rss()
        success = False
        error = None
        try:
            module = load_skill(skill_name)
            if module is None:
                return f"Skill '{skill_name}' not found."
            result = module.run()
            success = True
            return str(result)
        except Exception:
            error = traceback.format_exc()
            return f"Skill execution error: {error}"
        finally:
            self.telemetry.log_action(
                action="execute_skill",
                agent="meta_manager",
                success=success,
                duration_ms=(time.perf_counter() - started) * 1000,
                ram_before=ram_before,
                ram_after=self.telemetry.current_rss(),
                error=error,
            )

    # ─── Phase 3.5: Update Memory (The Heartbeat Modification) ───
    async def update_memory(self, new_content: str) -> str:
        await self.broadcast_state("reflecting", {"label": "Updating Agent Memory..."})
        heartbeat_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "heartbeat.md")
        try:
            with open(heartbeat_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return "✅ Successfully updated heartbeat.md. Memory state saved."
        except Exception as e:
            return f"❌ Failed to update memory: {e}"

    # ─── Phase 4: Analyze Codebase (The Nervous System) ───
    async def analyze_codebase(self, query: str = "", file_path: str = "") -> str:
        await self.broadcast_state("code_matrix", {"label": f"Scanning Codebase: {query or file_path}"})

        if file_path:
            content = repo.get_local_file(file_path)
            return f"📄 {file_path}:\n{content}"
        elif query:
            matches = repo.search_local_files(query)
            if not matches:
                return f"No files found matching '{query}'."
            lines = [f"🔍 Found {len(matches)} matches for '{query}':"]
            for m in matches:
                lines.append(f"  📄 {m['path']}:{m['line']} → {m['snippet']}")
            return "\n".join(lines)
        else:
            return repo.get_file_tree()

    # ─── Phase 5: Jules AI Dispatch (with codebase context injection) ───
    async def dispatch_to_jules(self, task_type: str, plan: str, context: str = "") -> str:
        await self.broadcast_state("jules_dispatching", {"label": f"Jules AI: {task_type.upper()} via MCPs..."})
        started = time.perf_counter()
        ram_before = self.telemetry.current_rss()
        success = False
        error = None

        try:
            # AUTO-INJECT: Find relevant codebase files to give Jules perfect context
            await self.broadcast_state("code_matrix", {"label": "Indexing relevant files for Jules..."})
            code_context = repo.get_relevant_context(plan[:200])
            enriched_context = f"{context}\n\n### LIVE CODEBASE CONTEXT:\n{code_context}"

            result = await jules.dispatch_task(task_type, plan, enriched_context)

            if result.get("success"):
                task_id = result.get("task_id", "N/A")
                await self.broadcast_state("reflecting", {"label": f"Waiting on Jules AI (Task: {task_id})..."})
                
                # Polling for completion
                status_data = await jules.poll_status(task_id, max_attempts=12, interval=15.0)
                final_status = status_data.get("status", "unknown")
                success = True
                
                # Verification Step
                repo_status = repo.get_git_status()
                prs = repo.list_open_prs()
                
                return (
                    f"🟢 Jules Task '{task_type}' finished with status: [{final_status}]\n\n"
                    f"### Output Logs:\n{status_data.get('message', 'No details.')}\n\n"
                    f"### Auto-Verification (Git):\n{repo_status}\n\n"
                    f"### Open PRs:\n{prs}"
                )
            msg = result.get("message", "Unknown error")
            error = msg
            preview = json.dumps(result.get("payload_preview", {}), indent=2)[:500]
            return f"⚠️ Jules dispatch status: {msg}\n\nPayload (for manual review):\n{preview}"
        except Exception as exc:
            error = str(exc)
            return f"⚠️ Jules dispatch error: {exc}"
        finally:
            self.telemetry.log_action(
                action="dispatch_to_jules",
                agent="jules",
                success=success,
                duration_ms=(time.perf_counter() - started) * 1000,
                ram_before=ram_before,
                ram_after=self.telemetry.current_rss(),
                error=error,
            )

    # ─── Phase 6: Web Search (Zero Dependency) ───
    async def search_web(self, query: str) -> str:
        await self.broadcast_state("reflecting", {"label": f"Searching Web: {query}"})
        started = time.perf_counter()
        ram_before = self.telemetry.current_rss()
        success = False
        error = None
        try:
            url = "https://html.duckduckgo.com/html/"
            payload = {'q': query}
            headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Chrome/100.0'}
            resp = requests.post(url, data=payload, headers=headers, timeout=10)
            if resp.status_code != 200:
                error = f"HTTP {resp.status_code}"
                return f"No search results found (HTTP {resp.status_code})"
                
            html = resp.text
            # Basic Regex extraction for ddg snippets
            snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', html, re.DOTALL | re.IGNORECASE)
            
            if not snippets:
                return "No search results found."
                
            formatted = []
            for s in snippets[:3]:
                clean_text = re.sub(r'<[^>]+>', '', s).strip()
                formatted.append(f"- {clean_text}")
            success = True
            return f"🌐 Web Search Results for '{query}':\n" + "\n\n".join(formatted)
        except Exception as e:
            error = str(e)
            return f"Search error: {e}"
        finally:
            self.telemetry.log_action(
                action="search_web",
                agent="meta_manager",
                success=success,
                duration_ms=(time.perf_counter() - started) * 1000,
                ram_before=ram_before,
                ram_after=self.telemetry.current_rss(),
                error=error,
            )

    # ─── Phase 7: Analyze Chat History Logs ───
    async def analyze_chat_logs(self, query: str = "") -> str:
        await self.broadcast_state("reflecting", {"label": "Reading past chat logs..."})
        log_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "logs", "chat_history.jsonl")
        if not os.path.exists(log_path):
            return "No previous chat logs found."
        
        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            # return last 20 entries
            recent = lines[-20:]
            history = []
            for l in recent:
                try:
                    data = json.loads(l)
                    history.append(f"[{data.get('timestamp')[:19]}] {data.get('role').upper()}: {data.get('content')[:200]}")
                except:
                    pass
            return "📜 Recent Chat Logs:\n" + "\n".join(history)
        except Exception as e:
            return f"Error reading logs: {e}"

    # ─── Phase 8: Reflection & Memory (Post-Task Learning) ───
    async def reflect_and_remember(self, user_query: str, result: str):
        """After every task, Groq summarizes lessons learned and saves to memory."""
        try:
            reflection_prompt = [
                {"role": "system", "content": "You are a concise engineering journal writer. Summarize what was learned from this task in 2-3 sentences. Focus on what worked, what failed, and what to do differently next time."},
                {"role": "user", "content": f"Task: {user_query}\n\nResult: {result[:1000]}"}
            ]
            resp = ai_client.chat_completion(
                messages=reflection_prompt,
                max_tokens=256
            )
            lesson = resp.choices[0].message.content

            # TODO: When sqlite-vec is fully operational, save the lesson embedding here.
            # For now, we append it to the conversation context so the agent remembers.
            self.conversation.append({
                "role": "system",
                "content": f"[MEMORY ENGRAM]: {lesson}"
            })
            return lesson
        except Exception:
            return None

    # ─── The Main Loop Entry Point ───
    async def process(self, user_text: str) -> str:
        """
        The full Meta-Loop cycle:
        Listen -> Reflect -> [Skill-Make | Execute | Jules | Speak] -> Remember -> Visualize
        """
        # Step 1: Reflect (Groq)
        decision = await self.reflect(user_text)
        action = decision.get("action", "speak")

        # Step 2: Route
        if action == "create_skill":
            result = await self.build_skill(
                decision.get("skill_name", "unnamed"),
                decision.get("description", ""),
                decision.get("python_code", "")
            )
        elif action == "execute_skill":
            result = await self.execute_skill(decision.get("skill_name", ""))
        elif action == "analyze_code":
            result = await self.analyze_codebase(
                query=decision.get("query", ""),
                file_path=decision.get("file_path", "")
            )
        elif action == "dispatch_jules":
            result = await self.dispatch_to_jules(
                decision.get("task_type", "general"),
                decision.get("architecture_plan", ""),
                decision.get("context", "")
            )
        elif action == "update_memory":
            result = await self.update_memory(decision.get("new_content", ""))
        elif action == "search_web":
            sub_res = await self.search_web(decision.get("query", ""))
            self.conversation.append({"role": "system", "content": f"WEB SEARCH RESULTS:\n{sub_res}"})
            final_res = await self.reflect("Synthesize the search results and answer my query.")
            result = final_res.get("text", sub_res)
        elif action == "analyze_chat_logs":
            sub_res = await self.analyze_chat_logs()
            self.conversation.append({"role": "system", "content": f"CHAT LOGS:\n{sub_res}"})
            final_res = await self.reflect("Analyze these chat logs to solve my problem.")
            result = final_res.get("text", sub_res)
        elif action == "build_saas":
            # Direct handover to SaaS State Machine
            project_name = decision.get("project_name", "MysteryProject")
            description = decision.get("description", user_text)
            price = decision.get("price", "$10/mo")
            
            project = self.saas.load_project(project_name)
            project.config.update({"description": description, "price": price})
            self.saas.save_project(project)
            
            result = await self.saas.advance_project(project_name)
        else:
            result = decision.get("text", "I have no response.")

        # Step 3: Broadcast final result to Hologram
        await self.broadcast_state("speaking", {"label": "Delivering Result", "result": result})

        # Step 4: Reflection & Memory
        await self.reflect_and_remember(user_text, result)

        # Return to idle
        await asyncio.sleep(0.5)
        await self.broadcast_state("idle")

        return result
