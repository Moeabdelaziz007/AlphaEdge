from dataclasses import dataclass


def configure(api_key: str = ""):
    return None


@dataclass
class _Resp:
    text: str


class GenerativeModel:
    def __init__(self, name: str):
        self.name = name

    def generate_content(self, prompt: str):
        return _Resp(text=f"Stub Gemini response for: {prompt[:120]}")
