from src.core.engine import CognitiveEngine
from src.memory.db import MemoryLayer
from src.state.manager import CognitiveState
from src.agents.generator import Generator
from src.agents.challenger import Challenger
from src.agents.synthesizer import Synthesizer
from rich.console import Console

console = Console()

class CognitivePipeline:
    """
    The Orchestrator. Unifies the Cognitive Agents, LLM Engine, and Vector DB
    into a zero-latency Context Switching loop. 
    """
    def __init__(self, engine: CognitiveEngine = None, memory: MemoryLayer = None):
        console.print("[cyan]Initializing TurboQuant Engine and SQLite-Vec Memory...[/cyan]")
        self.engine = engine or CognitiveEngine()
        self.memory = memory or MemoryLayer()
        
        self.generator = Generator(self.engine)
        self.challenger = Challenger(self.engine)
        self.synthesizer = Synthesizer(self.engine)

    def run(self, user_query: str) -> CognitiveState:
        console.print(f"\n[magenta]🧠 Initiating Cognitive Loop for:[/magenta] {user_query}")
        
        # 1. Memory Retrieval phase
        console.print("[dim]Retrieving long-term memory context...[/dim]")
        memories = self.memory.search_memory(user_query, top_k=3)
        
        state = CognitiveState(
            original_prompt=user_query,
            context_memories=memories
        )
        
        # 2. Generator Phase
        console.print("[yellow]⚙️  Phase 1: Generator Drafting...[/yellow]")
        draft = self.generator.generate(user_query, memories)
        state.generator_draft = draft
        console.print("[dim]- Draft completed.[/dim]")
        
        # 3. Challenger Phase
        console.print("[red]🛡️  Phase 2: Challenger Critiquing...[/red]")
        critique = self.challenger.critique(user_query, draft)
        state.challenger_critique = critique
        console.print("[dim]- Flaws isolated.[/dim]")
        
        # 4. Synthesizer Phase
        console.print("[green]🧬 Phase 3: Synthesizer Assembling...[/green]")
        final_result = self.synthesizer.synthesize(user_query, draft, critique)
        state.synthesized_result = final_result
        console.print("[dim]- Output refined and finalized.[/dim]")
        
        # 5. Archive to Long-term Memory
        console.print("[dim]Archiving final synthesis into Vector DB...[/dim]")
        self.memory.add_memory(f"Query: {user_query}\nResult: {final_result}")
        
        return state
