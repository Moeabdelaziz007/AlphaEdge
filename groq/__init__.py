"""Tiny local shim for groq SDK used in tests/offline CI."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, List, Optional


class RateLimitError(Exception):
    pass


class APIError(Exception):
    pass


@dataclass
class _Message:
    content: str
    tool_calls: Optional[list] = None


@dataclass
class _Choice:
    message: _Message


@dataclass
class _Response:
    choices: List[_Choice]


class _Completions:
    def create(self, messages: list, response_format: Optional[dict] = None, **kwargs: Any) -> _Response:
        user_prompt = ""
        for msg in reversed(messages):
            if isinstance(msg, dict) and msg.get("role") == "user":
                user_prompt = msg.get("content", "")
                break

        if response_format and response_format.get("type") == "json_object":
            content = json.dumps({"action": "speak", "text": "Offline mode active."})
        else:
            content = f"Offline Groq stub response: {user_prompt[:120]}" if user_prompt else "Offline Groq stub response."

        return _Response(choices=[_Choice(message=_Message(content=content, tool_calls=[]))])


class _Chat:
    def __init__(self) -> None:
        self.completions = _Completions()


class Groq:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.chat = _Chat()
