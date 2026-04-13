from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from hashlib import sha256
from pathlib import Path
import re
import traceback
from typing import Any, Iterable


@dataclass(slots=True)
class ErrorSignature:
    """Canonical fields extracted from a single exception instance."""

    error_class: str
    module: str
    stack_fingerprint: str
    message: str
    frames: tuple[str, ...] = ()


@dataclass(slots=True)
class ErrorCluster:
    """Group of similar failures sharing the same error fingerprint."""

    cluster_key: str
    error_class: str
    module: str
    stack_fingerprint: str
    count: int = 0
    sample_messages: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    pattern_axioms: list[str] = field(default_factory=list)



def _normalize_module(filename: str | None) -> str:
    if not filename:
        return "unknown"

    normalized = filename.replace("\\", "/")
    parts = [p for p in normalized.split("/") if p]
    if not parts:
        return "unknown"

    if "src" in parts:
        idx = parts.index("src")
        subpath = parts[idx + 1 :]
        if subpath:
            if subpath[-1].endswith(".py"):
                subpath[-1] = Path(subpath[-1]).stem
            return ".".join(subpath)

    leaf = parts[-1]
    return Path(leaf).stem if leaf.endswith(".py") else leaf



def _frame_tokens(tb: traceback.StackSummary) -> tuple[str, ...]:
    tokens: list[str] = []
    for frame in tb:
        module = _normalize_module(frame.filename)
        tokens.append(f"{module}:{frame.name}:{frame.lineno}")
    return tuple(tokens)



def extract_error_signature(exc: BaseException) -> ErrorSignature:
    """
    Extracts `error_class`, `module`, and `stack_fingerprint` from an exception.
    """

    tb = traceback.extract_tb(exc.__traceback__) if exc.__traceback__ else traceback.StackSummary()
    frames = _frame_tokens(tb)
    module = _normalize_module(tb[-1].filename) if tb else "unknown"
    error_class = exc.__class__.__name__
    message = str(exc)

    basis = "|".join((error_class, module, *frames))
    fingerprint = sha256(basis.encode("utf-8")).hexdigest()[:16]

    return ErrorSignature(
        error_class=error_class,
        module=module,
        stack_fingerprint=fingerprint,
        message=message,
        frames=frames,
    )



def _cluster_key(signature: ErrorSignature) -> str:
    return f"{signature.error_class}|{signature.module}|{signature.stack_fingerprint}"



def cluster_exceptions(exceptions: Iterable[BaseException]) -> list[ErrorCluster]:
    """Groups similar exceptions into recurring clusters."""

    buckets: dict[str, ErrorCluster] = {}

    for exc in exceptions:
        signature = extract_error_signature(exc)
        key = _cluster_key(signature)

        if key not in buckets:
            buckets[key] = ErrorCluster(
                cluster_key=key,
                error_class=signature.error_class,
                module=signature.module,
                stack_fingerprint=signature.stack_fingerprint,
            )

        cluster = buckets[key]
        cluster.count += 1
        if signature.message and signature.message not in cluster.sample_messages and len(cluster.sample_messages) < 3:
            cluster.sample_messages.append(signature.message)

    return sorted(
        buckets.values(),
        key=lambda c: (c.count, c.error_class, c.module),
        reverse=True,
    )



def _resolve_axiom_payload(payload: Any) -> tuple[str | None, str | None]:
    if isinstance(payload, str):
        return payload, None
    if isinstance(payload, dict):
        recommendation = payload.get("recommendation") or payload.get("fix") or payload.get("action")
        axiom_id = payload.get("axiom") or payload.get("id")
        return recommendation, axiom_id
    return None, None



def attach_auto_fix_recommendations(
    clusters: list[ErrorCluster],
    pattern_axioms: dict[str, Any],
) -> list[ErrorCluster]:
    """
    Auto-generates fix recommendations and links them to `pattern_axioms`.

    Matching rule: pattern key is treated as case-insensitive regex tested against
    `error_class`, `module`, and sample messages.
    """

    for cluster in clusters:
        searchable_text = " ".join(
            [cluster.error_class, cluster.module, " ".join(cluster.sample_messages)]
        ).lower()

        matched_axioms: set[str] = set()
        matched_recommendations: set[str] = set()

        for pattern, payload in pattern_axioms.items():
            if not pattern:
                continue
            if re.search(pattern.lower(), searchable_text):
                recommendation, axiom_id = _resolve_axiom_payload(payload)
                if recommendation:
                    matched_recommendations.add(recommendation)
                if axiom_id:
                    matched_axioms.add(axiom_id)
                else:
                    matched_axioms.add(pattern)

        if not matched_recommendations:
            matched_recommendations.add(
                "Reproduce with focused test, inspect latest stack frame, and add guardrails/validation at the failure boundary."
            )
            matched_axioms.add("fallback.general_resilience")

        cluster.recommendations = sorted(matched_recommendations)
        cluster.pattern_axioms = sorted(matched_axioms)

    return clusters



def top_recurring_failure_clusters(clusters: list[ErrorCluster], top_n: int = 5) -> str:
    """Builds prompt-ready text for dispatch workflows."""

    ranked = sorted(clusters, key=lambda c: c.count, reverse=True)[:top_n]
    if not ranked:
        return "Top recurring failure clusters: none observed."

    lines = ["Top recurring failure clusters:"]
    for idx, cluster in enumerate(ranked, start=1):
        sample_msg = cluster.sample_messages[0] if cluster.sample_messages else "n/a"
        lines.append(
            (
                f"{idx}. [{cluster.count}x] {cluster.error_class} @ {cluster.module} "
                f"(fingerprint={cluster.stack_fingerprint})\\n"
                f"   - sample: {sample_msg}\\n"
                f"   - pattern_axioms: {', '.join(cluster.pattern_axioms) or 'none'}\\n"
                f"   - recommended_fixes: {', '.join(cluster.recommendations) or 'none'}"
            )
        )
    return "\n".join(lines)



def build_error_intelligence_report(
    exceptions: Iterable[BaseException],
    pattern_axioms: dict[str, Any],
    top_n: int = 5,
) -> dict[str, Any]:
    """End-to-end helper for extraction, clustering, and dispatch-ready reporting."""

    clusters = cluster_exceptions(exceptions)
    clusters = attach_auto_fix_recommendations(clusters, pattern_axioms)
    dispatch_block = top_recurring_failure_clusters(clusters, top_n=top_n)

    by_module: dict[str, int] = defaultdict(int)
    for cluster in clusters:
        by_module[cluster.module] += cluster.count

    return {
        "clusters": [
            {
                "cluster_key": c.cluster_key,
                "error_class": c.error_class,
                "module": c.module,
                "stack_fingerprint": c.stack_fingerprint,
                "count": c.count,
                "sample_messages": c.sample_messages,
                "recommendations": c.recommendations,
                "pattern_axioms": c.pattern_axioms,
            }
            for c in clusters
        ],
        "top_modules": sorted(by_module.items(), key=lambda item: item[1], reverse=True),
        "dispatch_prompt_block": dispatch_block,
    }
