import os
import json
import asyncio
import requests
from src.core.ai_client import AIClient
from rich.console import Console
from src.core.jules_bridge import JulesAIClient

console = Console()
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))

# Gemini is configured lazily inside AlphaManagerAI.__init__ to respect .env load order.
gemini_model = None

# ---- MCP-STYLE TOOLS (Routing Groq -> Gemini & Jules) ----

def read_repository_file(relative_path: str) -> str:
    """MCP Tool: Read contents of any code file in the AlphaEdge repo strictly to audit it."""
    try:
        path = os.path.join(project_root, relative_path)
        with open(path, 'r', encoding='utf-8') as f:
            return f"FILE CONTENTS OF {relative_path}:\n{f.read()[:3000]}... (truncated)"
    except Exception as e:
        return f"File Error: {e}"

def invoke_gemini_deep_brain(query: str) -> str:
    """MCP Tool: Routs deep research, trends, and complex analysis to Gemini 1.5 Pro."""
    try:
        if not os.getenv("GEMINI_API_KEY"):
            return "[Gemini Gateway Offline]: Missing API Key."
        
        prompt = f"Perform deep heuristic research and provide Hidden Gems/Edge AI trends regarding: {query}"
        response = gemini_model.generate_content(prompt)
        return (f"[Gemini Deep Brain Executed]:\n{response.text}\n"
                "-> [System Directive]: Use this context to break down tasks.")
    except Exception as e:
        return f"[Gemini Error]: {e}"

async def trigger_jules_autonomous_agent(task_type: str, plan: str, context: str = "") -> str:
    """
    MCP Tool: The Singularity Gateway. 
    Triggers Jules AI via bridge to execute code and push PRs via MCPs.
    """
    jules = JulesAIClient()
    repo = os.getenv("GITHUB_REPO", "Moeabdelaziz007/AlphaEdge")
    
    result = await jules.dispatch_task(task_type, plan, context, repo=repo)
    
    if result.get("success"):
        return f"🟢 [Jules AI Triggered]: {result.get('message')} (Task ID: {result.get('task_id')})"
    else:
        return f"⚠️ [Jules AI Failed]: {result.get('message')}"

# Tool JSON schemas for Llama 3 Router
tools = [
    {
        "type": "function",
        "function": {
            "name": "read_repository_file",
            "description": "Read contents of any code file in the AlphaEdge repo.",
            "parameters": {
                "type": "object",
                "properties": { "relative_path": { "type": "string" } },
                "required": ["relative_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "invoke_gemini_deep_brain",
            "description": "Trigger Gemini when the user asks for deep web search, multimodal vision logic, or complex tech trends.",
            "parameters": {
                "type": "object",
                "properties": { "query": { "type": "string" } },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "trigger_jules_autonomous_agent",
            "description": "Trigger Jules AI to write the code. Use this ONLY after you have planned the architecture out.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_type": { "type": "string", "enum": ["ui", "database", "deployment", "tracking", "docs", "general"] },
                    "plan": { "type": "string", "description": "Highly precise Developer guidelines/prompts for Jules to execute." },
                    "context": { "type": "string", "description": "Optional extra context or error traces." }
                },
                "required": ["task_type", "plan"]
            }
        }
    }
]

# ----------------------------------------------

class AlphaManagerAI:
    """
    The Super Meta Loop Command Center 
    (Senses: Groq | Deep Brain: Gemini | Muscle: Jules AI)
    """
    def __init__(self, api_key: str = None):
        try:
            self.ai_client = AIClient(api_key=api_key)
        except ValueError as e:
            raise ValueError(f"AIClient Init Error: {e}")
            
        # Lazy-init Gemini (must happen AFTER .env is loaded by bot.py)
        global gemini_model
        gemini_key = os.getenv("GEMINI_API_KEY", "")
        if gemini_key and gemini_model is None:
            try:
                import google.generativeai as genai
                genai.configure(api_key=gemini_key)
                gemini_model = genai.GenerativeModel('gemini-1.5-flash')
                console.print("[green]✅ Gemini Deep Brain initialized.[/green]")
            except Exception as e:
                console.print(f"[yellow]⚠️ Gemini init failed: {e}[/yellow]")
        
        self.system_prompt = (
            "You are AlphaManager, the AI Co-Founder orchestrating the Super Meta Loop. "
            "You have 3 primary weapons: \n"
            "1. Groq (Your immediate logic parser) \n"
            "2. Gemini API (Your Deep Brain for search) \n"
            "3. Jules AI (Your Autonomous Coder via API webhook) \n\n"
            "AGENTIC RULES:\n"
            "1. You DO NOT write heavy code yourself. You command Jules to do it using `trigger_jules_autonomous_agent`.\n"
            "2. NEVER print fake XML-style tags like `<function=...>` or `<tool=...>`. Use the PROVIDED tool-calling API.\n"
            "3. If you 'lie' and say you triggered a tool without actually calling the system tool, you FAIL your objective.\n"
            "4. RATIONALE-FIRST: Before calling a tool, you MUST explain your logic in Arabic starting with 'التفكير:'.\n"
            "5. You MUST ALWAYS speak and converse entirely in Arabic (العربية).\n"
            "6. ANY reports you generate MUST be entirely in Arabic.\n\n"
            "Strategic Awareness:\n"
            "- We have a Predictive Watcher daemon monitoring file changes and blast radius.\n"
            "- We run locally on Apple Metal. Optimize for low memory overhead."
        )
        self.sessions = {}
        self._load_prompts_from_db()

    def _load_prompts_from_db(self):
        """Loads mutated system prompts from SQLite."""
        try:
            import sqlite3
            db_path = os.path.join(project_root, "data", "db", "memory.sqlite")
            with sqlite3.connect(db_path) as conn:
                cursor = conn.execute("SELECT content FROM mutated_prompts WHERE name = 'alpha_manager' ORDER BY id DESC LIMIT 1")
                row = cursor.fetchone()
                if row:
                    self.system_prompt = row[0]
                    console.print("[green]🧬 Self-Evolved Prompt Loaded from DB.[/green]")
        except Exception:
            pass

    async def _reflect_and_mutate(self, result: str, session_id: str):
        """Background task for self-critique."""
        if session_id == "system": return # Don't reflect on reflections
        
        try:
            # Simple heuristic score (in a real system, ask Groq to score it)
            score = 1.0
            if "Error" in result or "Failed" in result or "⚠️" in result:
                score = 0.2
            
            from src.core.daemons import ReflectionEngine
            engine = ReflectionEngine()
            engine.log_reflection(session_id, f"Outcome Analysis: {result[:200]}", score)
            
            if score < 0.5:
                # Potential mutation trigger
                console.print(f"[yellow]🧬 Performance drop detected in {session_id}. Reflection logged.[/yellow]")
        except Exception:
            pass

    def _get_history(self, session_id: str) -> list:
        if session_id not in self.sessions:
            self.sessions[session_id] = [{"role": "system", "content": self.system_prompt}]
        return self.sessions[session_id]

    def _prune_history(self, session_id: str, max_turns: int = 15):
        history = self.sessions.get(session_id, [])
        if len(history) > max_turns * 2:
            # Keep system prompt + last N turns
            system_msg = history[0]
            last_msgs = history[-(max_turns * 2):]
            self.sessions[session_id] = [system_msg] + last_msgs

    async def _execute_tool(self, tool_call) -> str:
        name = tool_call.function.name
        args = json.loads(tool_call.function.arguments)
        
        if name == "read_repository_file":
            return read_repository_file(args.get("relative_path"))
        elif name == "invoke_gemini_deep_brain":
            return invoke_gemini_deep_brain(args.get("query"))
        elif name == "trigger_jules_autonomous_agent":
            # For Jules tasks, we always want high capability tracking
            return await trigger_jules_autonomous_agent(args.get("task_type"), args.get("plan"), args.get("context", ""))
        return "Tool not found."
        
    async def process_request(self, user_text: str, session_id: str = "human", use_tools=True) -> str:
        history = self._get_history(session_id)
        history.append({"role": "user", "content": user_text})
        
        # High capability for automated sessions to prevent hallucinations
        require_high = session_id in ["heartbeat", "defi", "system"]
        
        try:
            kwargs = {
                "messages": history,
                "max_tokens": 2048,
                "require_high_capability": require_high
            }
            if use_tools:
                kwargs["tools"] = tools
                kwargs["tool_choice"] = "auto"

            attempts = 0
            max_sentinel_retries = 2
            
            while attempts <= max_sentinel_retries:
                response = self.ai_client.chat_completion(**kwargs)
                response_message = response.choices[0].message
                content = response_message.content or ""
                
                # Hallucination Sentinel: If it "speaks" code/results without calling tools
                has_fake_results = ("```" in content or "Result:" in content or "الناتج:" in content)
                if not response_message.tool_calls and has_fake_results and require_high:
                    console.print(f"[yellow]⚠️ Sentinel Trip in {session_id} (Attempt {attempts+1}). AI hallucinated results.[/yellow]")
                    history.append({"role": "assistant", "content": content})
                    history.append({
                        "role": "user", 
                        "content": "CRITICAL ERROR: You printed a code result or block but did NOT call any tools. You are a reasoning engine, not an executor. You MUST use trigger_jules_autonomous_agent or other tools to actually run code. DO NOT invent outputs."
                    })
                    attempts += 1
                    continue
                
                # Successfully didn't hallucinate or used tools
                break

            if response_message.tool_calls:
                history.append(response_message)
                for tool_call in response_message.tool_calls:
                    tool_result = await self._execute_tool(tool_call)
                    history.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": tool_call.function.name,
                        "content": tool_result,
                    })
                
                final_response = self.ai_client.chat_completion(
                    messages=history,
                    max_tokens=2048,
                    require_high_capability=require_high
                )
                output = final_response.choices[0].message.content or "No response from AI."
            else:
                output = response_message.content or "No response from AI."

            history.append({"role": "assistant", "content": output})
            # Trigger autonomous reflection
            asyncio.create_task(self._reflect_and_mutate(output, session_id))
            
            self._prune_history(session_id)
            return str(output)
            
        except Exception as e:
            return f"❌ AI Engine Error: {e}"

            
    async def generate_daily_report(self) -> str:
        try:
            with open(os.path.join(project_root, 'README.md'), 'r') as f:
                readme_content = f.read()[:2000]
        except Exception:
            readme_content = "AlphaEdge local state."
            
        prompt = (
            f"Generate an extremely concise System Health & Architecture Report.\n"
            f"CRITICAL: The report MUST be written entirely in Arabic (اللغة العربية).\n\n"
            f"Context from README:\n{readme_content}\n\n"
            "Structure:\n"
            "1. [الحالة] - Engine online. Rate limit protection active.\n"
            "2. [رؤى وأفكار من Gemini] - Strategic direction based on limits & repos.\n"
            "3. [المهام المجدولة لـ Jules] - What Jules should do next."
        )
        return await self.process_request(prompt, session_id="system", use_tools=True)

