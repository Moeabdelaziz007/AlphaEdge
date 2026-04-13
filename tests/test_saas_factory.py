import asyncio
import os
import sys

sys.path.append(os.getcwd())

from src.core.meta_manager import MetaManager


def test_saas_loop_transitions_to_infra():
    os.environ.setdefault("GROQ_API_KEY", "test-key")
    meta = MetaManager()
    orchestrator = meta.saas

    project_name = "TestSummarizer"
    project = orchestrator.load_project(project_name)
    project.config.update({
        "description": "A tool that summarizes long videos for marketers.",
        "price": "$15/mo",
    })
    orchestrator.save_project(project)

    asyncio.run(orchestrator.advance_project(project_name))
    updated = orchestrator.load_project(project_name)
    assert updated.state in {"infra", "cognition"}
