from src.core.engine import CognitiveEngine

class Challenger:
    """
    Phase 2 of Cognitive Context Switching: Logic Stress-Testing.
    Runs at extremely low temperature for deterministic, ruthless critiquing.
    """
    def __init__(self, engine: CognitiveEngine):
        self.engine = engine
        self.system_prompt = """
        You are the 'Challenger', a ruthless Senior Logic & Security Engineer.
        Your ONLY job is to critique the Generator's draft.
        Tear it apart. Find security flaws, logic gaps, edge cases, and performance bottlenecks.
        Be extremely analytical, harsh, and precise. DO NOT rewrite the code, only point out flaws.
        """

    def critique(self, user_query: str, generator_draft: str) -> str:
        prompt = f"Original Query: {user_query}\n\nGenerator Draft:\n{generator_draft}\n\nProvide a strict logic and security critique. Focus on finding vulnerabilities and bad practices:"
        return self.engine.generate(
            prompt=prompt, 
            system_prompt=self.system_prompt, 
            temperature=0.1
        )

    def hijack_prompt(self, new_prompt: str):
        """Temporarily overwrite agent persona for Autonomous TDD Arena."""
        self.system_prompt = new_prompt
