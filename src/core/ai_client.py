"""
Unified AI Client with Smart Fallback & Rate Limit Awareness.
Ensures the AlphaEdge Meta-Loop never crashes due to API limits.
"""
import os
import json
import logging
from typing import Optional, Dict, Any, List
from groq import Groq, RateLimitError, APIError

logger = logging.getLogger(__name__)

class AIClient:
    """
    Intelligent wrapper around Groq (and optionally Gemini) APIs.
    Implements cascading model fallback when rate limits (429) occur.
    """
    
    # Model hierarchy ordered by capability and resource cost.
    # NOTE: mixtral-8x7b-32768 was deprecated by Groq and now returns 404; it has been removed.
    GROQ_MODELS = [
        "llama-3.3-70b-versatile",    # Primary intelligence
        "llama-3.1-8b-instant",       # High-speed fallback
        "gemma2-9b-it",               # Lightweight fallback
    ]

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is not set.")
        
        self.client = Groq(api_key=self.api_key)
        self.current_model_idx = 0

    def chat_completion(self, messages: List[Dict[str, str]], require_high_capability: bool = False, **kwargs) -> Any:
        """
        Executes a chat completion request with automatic model fallback.
        Accepts standard Groq kwargs (e.g., max_tokens, tools, response_format).
        'require_high_capability' forces the use of only 70B+ models.
        """
        attempts = 0
        
        # If high capability is required, we only use the first 2 models (70B+)
        models_to_try = self.GROQ_MODELS[:2] if require_high_capability else self.GROQ_MODELS
        max_attempts = len(models_to_try)
        
        while attempts < max_attempts:
            # Use attempts index to rotate through models_to_try
            model = models_to_try[attempts % len(models_to_try)]
            try:
                active_kwargs = kwargs.copy()
                active_kwargs["model"] = model
                # Force zero-temperature for deterministic reliability
                active_kwargs["temperature"] = active_kwargs.get("temperature", 0.0)
                
                response = self.client.chat.completions.create(
                    messages=messages,
                    **active_kwargs
                )
                
                return response

            except RateLimitError as e:
                logger.warning(f"Rate limit hit on {model}: {e}. Switching to next fallback.")
                attempts += 1
            
            except APIError as e:
                logger.error(f"API Error on {model}: {e}. Attempting fallback.")
                attempts += 1
                
            except Exception as e:
                logger.error(f"Unexpected error in AIClient: {e}")
                raise e

        # Final failure
        raise Exception(f"AI Capacity Exhausted: All relevant models {'(70B+)' if require_high_capability else ''} failed.")
