import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.append(os.getcwd())


from src.core.evolution_loop import EvolutionLoop, KPI


def test_hypothesis_generation_and_rollout_sampling(tmp_path):
    loop = EvolutionLoop(db_path=str(tmp_path / "evolution.sqlite"), rollout_ratio=0.2)

    hypotheses = loop.generate_hypotheses()
    assert len(hypotheses) == 3
    assert {h.change_type for h in hypotheses} == {"prompt_tweak", "routing_tweak", "retry_policy"}

    sampled = sum(loop.should_apply_to_task(f"task-{i}") for i in range(1000))
    # Deterministic hash sampling should be near the configured rollout.
    assert 130 <= sampled <= 270


def test_auto_adopt_after_consistent_improvement(tmp_path):
    loop = EvolutionLoop(db_path=str(tmp_path / "evolution.sqlite"), required_streak=2)
    hypothesis = loop.generate_hypotheses()[0]

    baseline = KPI(latency_ms=1000, success_rate=0.91, cost_per_token=0.0020, rollback_rate=0.03)
    candidate = KPI(latency_ms=960, success_rate=0.918, cost_per_token=0.00195, rollback_rate=0.027)

    start = datetime.now(timezone.utc)
    r1 = loop.evaluate_and_record("exp-1", hypothesis, baseline, candidate, start, start + timedelta(minutes=5))
    assert r1.improved is True
    assert r1.adopted is False
    assert r1.streak == 1

    r2 = loop.evaluate_and_record("exp-1", hypothesis, baseline, candidate, start, start + timedelta(minutes=10))
    assert r2.improved is True
    assert r2.adopted is True
    assert r2.streak == 2

    history = loop.get_experiment_history(hypothesis.hypothesis_id)
    assert len(history) == 2
    assert history[0]["adopted"] == 1
    assert history[1]["adopted"] == 0