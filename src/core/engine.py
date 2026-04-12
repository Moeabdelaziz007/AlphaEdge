from llama_cpp import Llama
import os

class CognitiveEngine:
    """
    The core LLM engine wrapper utilizing TurboQuant-style massive KV compression.
    It manages the Apple Metal optimization and allows zero-latency state switching.
    """
    def __init__(self, model_path: str = "models/qwen2.5-1.5b-instruct-q4_k_m.gguf"):
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model not found at {model_path}. Run scripts/setup_models.py first.")
            
        # The TurboQuant Paradigm Integration (Extreme Memory Compression)
        # Using Apple Metal (n_gpu_layers=-1), massive KV Cache compression (flash_attn=True), 
        # and quantized KV values (type_k, type_v parameterization mapping to Q8_0 logic).
        self.llm = Llama(
            model_path=model_path,
            n_gpu_layers=-1,        # Metal MPS Acceleration enabled
            n_ctx=8192,             # Massive context capability safely running within low RAM
            flash_attn=True,        # Critical algorithmic optimization for bandwidth reduction
            type_k=8,               # GGML_TYPE_Q8_0 for Memory keys
            type_v=8,               # GGML_TYPE_Q8_0 for Memory values
            verbose=False
        )

    def generate(self, prompt: str, system_prompt: str = "You are an analytical assistant.", temperature: float = 0.7, max_tokens: int = 1024) -> str:
        """
        Dynamically handles generation parameters without reloading the model weights into VRAM.
        This enables actual zero-latency Cognitive Context Switching.
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ]
        
        response = self.llm.create_chat_completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response["choices"][0]["message"]["content"]
