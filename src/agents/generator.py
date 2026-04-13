from src.core.engine import CognitiveEngine

class Generator:
    """
    Phase 1 of Cognitive Context Switching: Idea Generation.
    Runs at higher temperature for creativity and unbounded drafting.
    """
    def __init__(self, engine: CognitiveEngine):
        self.engine = engine
        self.system_prompt = """
        You are the 'Generator' in a cognitive context switching loop.
        Your task is to produce the best initial draft, solution, or code based on the user query.
        Be creative, bold, and comprehensive. Provide solid starting structures.
        Rely on the provided Context Memories to tailor your response.
        """

    def generate(self, user_query: str, context_memories: list) -> str:
        ctx_str = "\n".join(context_memories) if context_memories else "No prior memories."
        prompt = f"Context Memories:\n{ctx_str}\n\nTask:\n{user_query}\n\nDraft a comprehensive solution:"
        return self.engine.generate(
            prompt=prompt, 
            system_prompt=self.system_prompt, 
            temperature=0.7
        )

    def hijack_prompt(self, new_prompt: str):
        """Temporarily overwrite agent persona for Autonomous TDD Arena."""
        self.system_prompt = new_prompt
