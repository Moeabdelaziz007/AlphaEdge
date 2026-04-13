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
    
    # Model hierarchy ordered by capability and resource cost
    GROQ_MODELS = [
        "llama-3.3-70b-versatile",    # Primary intelligence
        "llama-3.1-70b-versatile",    # Fallback intelligence
        "llama-3.1-8b-instant",       # High-speed fallback
        "mixtral-8x7b-32768",         # High context fallback
        "gemma2-9b-it"                # Absolute last resort
    ]

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY is not set.")
        
        self.client = Groq(api_key=self.api_key)
        self.current_model_idx = 0

    def chat_completion(self, messages: List[Dict[str, str]], **kwargs) -> Any:
        """
        Executes a chat completion request with automatic model fallback.
        Accepts standard Groq kwargs (e.g., max_tokens, tools, response_format).
        """
        original_model_idx = self.current_model_idx
        attempts = 0
        max_attempts = len(self.GROQ_MODELS)
        
        while attempts < max_attempts:
            model = self.GROQ_MODELS[self.current_model_idx]
            try:
                # Force clean kwargs
                active_kwargs = kwargs.copy()
                active_kwargs["model"] = model
                
                response = self.client.chat.completions.create(
                    messages=messages,
                    **active_kwargs
                )
                
                # If we succeeded with a fallback model, maybe log it.
                if self.current_model_idx != original_model_idx:
                    logger.info(f"Successfully recovered using fallback model: {model}")
                
                return response

            except RateLimitError as e:
                logger.warning(f"Rate limit hit on {model}: {e}. Switching to next fallback.")
                self.current_model_idx = (self.current_model_idx + 1) % len(self.GROQ_MODELS)
                attempts += 1
            
            except APIError as e:
                # Handle unexpected API failures (e.g. 503 Service Unavailable) by falling back too
                logger.error(f"API Error on {model}: {e}. Attempting fallback.")
                self.current_model_idx = (self.current_model_idx + 1) % len(self.GROQ_MODELS)
                attempts += 1
                
            except Exception as e:
                # Other exceptions (like parsing or network complete breaks) bubble up
                logger.error(f"Unexpected error in AIClient: {e}")
                raise e

        # If we exhausted all models
        raise Exception("All Groq models exhausted or rate limited. Meta-Loop stalled.")
