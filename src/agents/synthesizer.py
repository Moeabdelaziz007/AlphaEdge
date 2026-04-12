from src.core.engine import CognitiveEngine

class Synthesizer:
    """
    Phase 3 of Cognitive Context Switching: Executive Synthesis.
    Runs at medium temperature to merge creative draft with strict logic evaluation.
    """
    def __init__(self, engine: CognitiveEngine):
        self.engine = engine
        self.system_prompt = """
        You are the 'Synthesizer', the ultimate decision-maker and lead architect.
        You receive the original query, the Generator's creative draft, and the Challenger's ruthless critique.
        Your job is to weave them together, resolving the outlined flaws and keeping the best ideas, to output the final, flawless result.
        Output ONLY the final, polished result and a brief summary of how it was architecturally improved.
        """

    def synthesize(self, user_query: str, generator_draft: str, challenger_critique: str) -> str:
        prompt = f"Original Query: {user_query}\n\nGenerator Draft:\n{generator_draft}\n\nChallenger Critique:\n{challenger_critique}\n\nSynthesize the final flawless solution:"
        return self.engine.generate(
            prompt=prompt, 
            system_prompt=self.system_prompt, 
            temperature=0.4
        )
