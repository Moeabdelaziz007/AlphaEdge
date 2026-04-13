# The AlphaEdge Skill Registry
# This directory is populated AUTONOMOUSLY by the Meta-Manager.
# Each .py file represents a learned capability.
# DO NOT manually edit files here - the AI writes, tests, and registers them.

import os
import importlib
import importlib.util

SKILLS_DIR = os.path.dirname(os.path.abspath(__file__))

def list_skills():
    """Returns all registered skill module names."""
    return [f[:-3] for f in os.listdir(SKILLS_DIR) if f.endswith('.py') and f != '__init__.py']

def load_skill(skill_name: str):
    """Dynamically imports and returns a skill module."""
    path = os.path.join(SKILLS_DIR, f"{skill_name}.py")
    if not os.path.exists(path):
        return None
    spec = importlib.util.spec_from_file_location(skill_name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
