"""Lightweight local fallback for python-dotenv used in offline environments."""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional


def load_dotenv(dotenv_path: Optional[str] = None, override: bool = False) -> bool:
    """Load key=value pairs from a .env file into ``os.environ``.

    Returns ``True`` when a file is found and parsed, otherwise ``False``.
    """
    path = Path(dotenv_path) if dotenv_path else Path.cwd() / ".env"
    if not path.exists() or not path.is_file():
        return False

    loaded_any = False
    for raw_line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if not key:
            continue

        if override or key not in os.environ:
            os.environ[key] = value
            loaded_any = True

    return loaded_any
