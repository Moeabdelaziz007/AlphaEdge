"""Telemetry utilities for MetaManager sensitive operations."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

import psutil


class TelemetryLogger:
    """Collects runtime telemetry events into an in-memory store."""

    def __init__(self, store: Optional[list[dict[str, Any]]] = None):
        self.store = store if store is not None else []
        self._process = psutil.Process()

    def current_rss(self) -> int:
        """Return the current RSS memory usage in bytes."""
        return self._process.memory_info().rss

    def log_action(
        self,
        *,
        action: str,
        agent: str,
        success: bool,
        duration_ms: float,
        ram_before: int,
        ram_after: int,
        tokens_used: Optional[int] = None,
        error: Optional[str] = None,
    ) -> dict[str, Any]:
        """Persist one telemetry event and return it."""
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "agent": agent,
            "success": success,
            "duration_ms": round(duration_ms, 3),
            "tokens_used": tokens_used,
            "ram_before": ram_before,
            "ram_after": ram_after,
            "ram_spike": ram_after - ram_before,
            "error": error,
        }
        self.store.append(event)
        return event
