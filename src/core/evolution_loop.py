import hashlib
import json
import os
import sqlite3
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class Hypothesis:
    """A small safe change candidate that can be rolled out progressively."""

    hypothesis_id: str
    change_type: str
    description: str
    patch: Dict[str, Any]


@dataclass(frozen=True)
class KPI:
    """KPI snapshot for one evaluation window."""

    latency_ms: float
    success_rate: float
    cost_per_token: float
    rollback_rate: float


@dataclass(frozen=True)
class EvaluationResult:
    """Comparison result between baseline and candidate for one time window."""

    improved: bool
    adopted: bool
    streak: int
    reasons: List[str]


class EvolutionLoop:
    """
    Continuous micro-evolution loop:
    1) Generate tiny hypotheses.
    2) Apply them to a small traffic percentage.
    3) Compare KPI windows.
    4) Auto-adopt only after sustained improvement.
    5) Persist every evaluation in `evolution_experiments`.
    """

    def __init__(
        self,
        db_path: str = "data/db/evolution.sqlite",
        rollout_ratio: float = 0.1,
        required_streak: int = 3,
    ) -> None:
        if rollout_ratio <= 0 or rollout_ratio >= 1:
            raise ValueError("rollout_ratio must be between 0 and 1 (exclusive).")
        if required_streak < 1:
            raise ValueError("required_streak must be >= 1")

        self.db_path = db_path
        self.rollout_ratio = rollout_ratio
        self.required_streak = required_streak

        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.db = sqlite3.connect(db_path)
        self.db.row_factory = sqlite3.Row
        self._ensure_tables()

        # in-memory streak tracker per hypothesis id
        self._streaks: Dict[str, int] = {}

    def _ensure_tables(self) -> None:
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS evolution_experiments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                experiment_name TEXT NOT NULL,
                hypothesis_id TEXT NOT NULL,
                change_type TEXT NOT NULL,
                hypothesis_json TEXT NOT NULL,
                window_start TEXT NOT NULL,
                window_end TEXT NOT NULL,
                rollout_ratio REAL NOT NULL,
                baseline_latency_ms REAL NOT NULL,
                candidate_latency_ms REAL NOT NULL,
                baseline_success_rate REAL NOT NULL,
                candidate_success_rate REAL NOT NULL,
                baseline_cost_per_token REAL NOT NULL,
                candidate_cost_per_token REAL NOT NULL,
                baseline_rollback_rate REAL NOT NULL,
                candidate_rollback_rate REAL NOT NULL,
                improved INTEGER NOT NULL,
                streak INTEGER NOT NULL,
                adopted INTEGER NOT NULL,
                reasons TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        self.db.commit()

    def generate_hypotheses(self, base_config: Optional[Dict[str, Any]] = None) -> List[Hypothesis]:
        """Generate small improvement hypotheses across prompt/routing/retry policies."""
        base_config = base_config or {}

        return [
            Hypothesis(
                hypothesis_id="prompt_tweak_concise_v1",
                change_type="prompt_tweak",
                description="Add concise reasoning hint and explicit output format.",
                patch={
                    "system_prompt_suffix": "Answer concisely. Return structured JSON when relevant.",
                    "temperature": min(base_config.get("temperature", 0.7), 0.6),
                },
            ),
            Hypothesis(
                hypothesis_id="routing_tweak_latency_v1",
                change_type="routing_tweak",
                description="Route short/simple tasks to cheaper faster model tier.",
                patch={
                    "router": {
                        "simple_task_max_tokens": 350,
                        "simple_task_target": "fast_tier",
                        "fallback_target": "quality_tier",
                    }
                },
            ),
            Hypothesis(
                hypothesis_id="retry_policy_backoff_v1",
                change_type="retry_policy",
                description="Use bounded retries with exponential backoff and jitter.",
                patch={
                    "retry": {
                        "max_attempts": 2,
                        "backoff_ms": [120, 280],
                        "jitter_ms": 40,
                        "retry_on": ["timeout", "rate_limit"],
                    }
                },
            ),
        ]

    def should_apply_to_task(self, task_id: str, rollout_ratio: Optional[float] = None) -> bool:
        """Deterministically sample a small percentage of tasks for candidate rollout."""
        ratio = self.rollout_ratio if rollout_ratio is None else rollout_ratio
        if ratio <= 0 or ratio >= 1:
            raise ValueError("rollout ratio must be between 0 and 1 (exclusive)")

        bucket = int(hashlib.md5(task_id.encode("utf-8"), usedforsecurity=False).hexdigest(), 16) % 10_000
        return bucket < int(ratio * 10_000)

    def evaluate_and_record(
        self,
        experiment_name: str,
        hypothesis: Hypothesis,
        baseline: KPI,
        candidate: KPI,
        window_start: datetime,
        window_end: datetime,
    ) -> EvaluationResult:
        """
        Evaluate KPI delta for a time window and auto-adopt only after sustained improvement.
        """
        improved, reasons = self._is_improved(baseline, candidate)

        current_streak = self._streaks.get(hypothesis.hypothesis_id, 0)
        new_streak = current_streak + 1 if improved else 0
        self._streaks[hypothesis.hypothesis_id] = new_streak

        adopted = improved and new_streak >= self.required_streak

        self.db.execute(
            """
            INSERT INTO evolution_experiments (
                experiment_name,
                hypothesis_id,
                change_type,
                hypothesis_json,
                window_start,
                window_end,
                rollout_ratio,
                baseline_latency_ms,
                candidate_latency_ms,
                baseline_success_rate,
                candidate_success_rate,
                baseline_cost_per_token,
                candidate_cost_per_token,
                baseline_rollback_rate,
                candidate_rollback_rate,
                improved,
                streak,
                adopted,
                reasons,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                experiment_name,
                hypothesis.hypothesis_id,
                hypothesis.change_type,
                json.dumps(asdict(hypothesis), ensure_ascii=False),
                self._iso(window_start),
                self._iso(window_end),
                self.rollout_ratio,
                baseline.latency_ms,
                candidate.latency_ms,
                baseline.success_rate,
                candidate.success_rate,
                baseline.cost_per_token,
                candidate.cost_per_token,
                baseline.rollback_rate,
                candidate.rollback_rate,
                int(improved),
                new_streak,
                int(adopted),
                json.dumps(reasons, ensure_ascii=False),
                self._iso(datetime.now(timezone.utc)),
            ),
        )
        self.db.commit()

        return EvaluationResult(improved=improved, adopted=adopted, streak=new_streak, reasons=reasons)

    def _is_improved(self, baseline: KPI, candidate: KPI) -> Tuple[bool, List[str]]:
        """
        Improvement rule:
        - success_rate must increase by >= 0.5 percentage points.
        - latency/cost/rollback must not regress by > 2%.
        - at least one of latency/cost/rollback must improve by >= 1%.
        """
        reasons: List[str] = []

        success_delta = candidate.success_rate - baseline.success_rate
        latency_delta = self._pct_delta(baseline.latency_ms, candidate.latency_ms)  # lower is better
        cost_delta = self._pct_delta(baseline.cost_per_token, candidate.cost_per_token)
        rollback_delta = self._pct_delta(baseline.rollback_rate, candidate.rollback_rate)

        if success_delta < 0.005:
            reasons.append("success_rate improvement below 0.5pp threshold")

        regressions = [
            ("latency", latency_delta > 0.02),
            ("cost/token", cost_delta > 0.02),
            ("rollback_rate", rollback_delta > 0.02),
        ]
        for metric_name, regressed in regressions:
            if regressed:
                reasons.append(f"{metric_name} regressed by more than 2%")

        efficiency_improved = any([
            latency_delta <= -0.01,
            cost_delta <= -0.01,
            rollback_delta <= -0.01,
        ])
        if not efficiency_improved:
            reasons.append("no >=1% improvement in latency/cost/rollback")

        improved = len(reasons) == 0
        if improved:
            reasons.append("candidate beats baseline and passes guardrails")

        return improved, reasons

    @staticmethod
    def _pct_delta(baseline_value: float, candidate_value: float) -> float:
        if baseline_value == 0:
            return 0.0
        return (candidate_value - baseline_value) / baseline_value

    @staticmethod
    def _iso(ts: datetime) -> str:
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return ts.astimezone(timezone.utc).isoformat()

    def get_experiment_history(self, hypothesis_id: Optional[str] = None) -> List[Dict[str, Any]]:
        cursor = self.db.cursor()
        if hypothesis_id:
            rows = cursor.execute(
                "SELECT * FROM evolution_experiments WHERE hypothesis_id = ? ORDER BY id DESC",
                (hypothesis_id,),
            ).fetchall()
        else:
            rows = cursor.execute("SELECT * FROM evolution_experiments ORDER BY id DESC").fetchall()

        return [dict(row) for row in rows]

    def close(self) -> None:
        self.db.close()
