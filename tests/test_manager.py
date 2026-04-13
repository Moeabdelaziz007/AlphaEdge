"""Deterministic unit tests for AlphaManager flows."""
import asyncio
import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.manager.intelligence import AlphaManagerAI


def _make_manager() -> AlphaManagerAI:
    os.environ.setdefault("GROQ_API_KEY", "test-key")
    return AlphaManagerAI(api_key="test-key")


def test_env_vars_present_or_stubbed():
    required = ["GROQ_API_KEY", "GEMINI_API_KEY", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"]
    os.environ.setdefault("GROQ_API_KEY", "stub")
    os.environ.setdefault("GEMINI_API_KEY", "stub")
    os.environ.setdefault("TELEGRAM_BOT_TOKEN", "stub")
    os.environ.setdefault("TELEGRAM_CHAT_ID", "stub")
    for var in required:
        assert os.getenv(var)


def test_report_generation_returns_text():
    manager = _make_manager()
    report = asyncio.run(manager.generate_daily_report())
    assert isinstance(report, str)
    assert report.strip() != ""


def test_meta_loop_routing_returns_text():
    manager = _make_manager()
    response = asyncio.run(
        manager.process_request(
            "Read the file src/core/engine.py and tell me what model it loads.",
            use_tools=True,
        )
    )
    assert isinstance(response, str)
    assert response.strip() != ""
