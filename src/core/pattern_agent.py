from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional


@dataclass
class AxiomEvidence:
    """Structured evidence snapshot used to score a candidate axiom."""

    cases: int = 0
    failure_rate: float = 0.0
    effect_size: float = 0.0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class PatternAgent:
    """
    Maintains and evolves pattern axioms from observed outcomes.

    Axioms progress through statuses:
    - candidate: insufficient or early support
    - verified: statistically supported and eligible for system-intuition injection
    - deprecated: stale or no longer supported by recent evidence
    """

    MIN_CASES = 20
    MIN_FAILURE_RATE = 0.15
    MIN_EFFECT_SIZE = 0.10

    VERIFIED_CONFIDENCE = 0.75
    DEPRECATION_CONFIDENCE = 0.30

    STALE_DAYS = 30
    RETIRE_DAYS = 90
    DECAY_PER_STALE_CYCLE = 0.08

    def __init__(self) -> None:
        self.pattern_axioms: List[Dict[str, Any]] = []

    def validate_axiom(self, evidence: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate that an axiom has minimum statistical support.

        The axiom is considered statistically supported if at least one of the
        following signals is present at/above threshold:
        - sufficient number of cases
        - measurable failure rate
        - clear effect-size difference
        """
        cases = int(evidence.get("cases", 0) or 0)
        failure_rate = float(evidence.get("failure_rate", 0.0) or 0.0)
        effect_size = abs(float(evidence.get("effect_size", 0.0) or 0.0))

        reasons = []
        if cases >= self.MIN_CASES:
            reasons.append("cases")
        if failure_rate >= self.MIN_FAILURE_RATE:
            reasons.append("failure_rate")
        if effect_size >= self.MIN_EFFECT_SIZE:
            reasons.append("effect_size")

        return {
            "is_valid": bool(reasons),
            "reasons": reasons,
            "cases": cases,
            "failure_rate": failure_rate,
            "effect_size": effect_size,
        }

    def upsert_axiom(self, name: str, statement: str, evidence: Dict[str, Any]) -> Dict[str, Any]:
        """Insert or update an axiom with confidence and lifecycle status."""
        now = datetime.now(timezone.utc)
        validation = self.validate_axiom(evidence)

        confidence_inputs = [
            min(validation["cases"] / max(self.MIN_CASES, 1), 1.0),
            min(validation["failure_rate"] / max(self.MIN_FAILURE_RATE, 1e-9), 1.0),
            min(validation["effect_size"] / max(self.MIN_EFFECT_SIZE, 1e-9), 1.0),
        ]
        confidence = round(sum(confidence_inputs) / len(confidence_inputs), 3)

        status = "verified" if validation["is_valid"] and confidence >= self.VERIFIED_CONFIDENCE else "candidate"

        record = self._find_axiom(name)
        if record is None:
            record = {
                "name": name,
                "statement": statement,
                "evidence": evidence,
                "confidence": confidence,
                "status": status,
                "created_at": now,
                "updated_at": now,
                "last_supported_at": now if validation["is_valid"] else None,
                "support_history": [
                    {
                        "at": now,
                        "validation": validation,
                        "confidence": confidence,
                    }
                ],
            }
            self.pattern_axioms.append(record)
            return record

        record["statement"] = statement
        record["evidence"] = evidence
        record["confidence"] = confidence
        record["updated_at"] = now
        if validation["is_valid"]:
            record["last_supported_at"] = now
            record["status"] = "verified" if confidence >= self.VERIFIED_CONFIDENCE else "candidate"
        elif record.get("status") != "deprecated":
            record["status"] = "candidate"

        record.setdefault("support_history", []).append(
            {"at": now, "validation": validation, "confidence": confidence}
        )
        return record

    def build_system_intuition_block(self) -> str:
        """Inject only verified axioms into SYSTEM INTUITION context."""
        verified_axioms = [a for a in self.pattern_axioms if a.get("status") == "verified"]
        if not verified_axioms:
            return "[SYSTEM INTUITION]\n- No verified axioms available yet."

        lines = ["[SYSTEM INTUITION]"]
        for axiom in verified_axioms:
            lines.append(
                f"- {axiom['name']}: {axiom['statement']} "
                f"(confidence={axiom['confidence']:.2f}, status={axiom['status']})"
            )
        return "\n".join(lines)

    def decay_and_retire(self, now: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Decay stale axioms and retire very old unsupported ones.

        Returns a list of records that changed state.
        """
        now = now or datetime.now(timezone.utc)
        changed: List[Dict[str, Any]] = []

        for axiom in self.pattern_axioms:
            last_supported_at = axiom.get("last_supported_at") or axiom.get("updated_at")
            if not isinstance(last_supported_at, datetime):
                continue

            age = now - last_supported_at
            previous_status = axiom.get("status")
            previous_confidence = float(axiom.get("confidence", 0.0))

            if age >= timedelta(days=self.STALE_DAYS):
                stale_cycles = max(age.days // self.STALE_DAYS, 1)
                decayed = max(previous_confidence - (stale_cycles * self.DECAY_PER_STALE_CYCLE), 0.0)
                axiom["confidence"] = round(decayed, 3)

                if axiom["confidence"] < self.DEPRECATION_CONFIDENCE:
                    axiom["status"] = "deprecated"
                elif axiom.get("status") == "verified":
                    axiom["status"] = "candidate"

            if age >= timedelta(days=self.RETIRE_DAYS):
                axiom["status"] = "deprecated"

            if axiom.get("status") != previous_status or axiom.get("confidence") != previous_confidence:
                axiom["updated_at"] = now
                changed.append(axiom)

        return changed

    def _find_axiom(self, name: str) -> Optional[Dict[str, Any]]:
        for axiom in self.pattern_axioms:
            if axiom.get("name") == name:
                return axiom
        return None
