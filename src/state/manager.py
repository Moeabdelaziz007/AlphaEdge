from pydantic import BaseModel, Field
from typing import Optional, List

class CognitiveState(BaseModel):
    """
    Tracks the entire lifecycle of the Cognitive Context Switching loop.
    Ensures state integrity across the Generator, Challenger, and Synthesizer phases.
    """
    # Phase 0: Injection
    original_prompt: str = Field(..., description="The user's initial core problem.")
    context_memories: List[str] = Field(default_factory=list, description="Relevant memories retrieved from via sqlite-vec.")
    
    # Phase 1: Generation
    generator_draft: Optional[str] = Field(None, description="The initial raw thought process or code draft.")
    
    # Phase 2: Refinement
    challenger_critique: Optional[str] = Field(None, description="Logical flaws, optimizations, and issues found by the Challenger.")
    
    # Phase 3: Synthesis
    synthesized_result: Optional[str] = Field(None, description="The final polished result combining the draft and critique.")
    
    def is_complete(self) -> bool:
        return self.synthesized_result is not None
