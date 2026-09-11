from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from pearl.environments.enterprise25 import (
    create_e01_baseline_policy,
    create_e01_evaluators,
    create_e01_runtime,
)
from pearl.evaluators import (
    Evaluator,
    LegacyGnomonJudgeEvaluator,
    evaluate_run,
    evaluate_trajectory,
)
from pearl.runtime.artifacts import ArtifactStoreError, JsonlArtifactStore
from pearl.runtime.runner import RunBundle, run_batch
from pearl.scenarios import load_scenario_distribution
from pearl.spec import (
    EvaluationBundle,
    EvaluationResult,
    EvaluationVector,
    EvaluatorReference,
    Partition,
    Reward,
    Scenario,
    Trajectory,
    aggregate_reward,
    load_environment_spec,
)

DIMENSIONS = (
    "task_success",
    "grounding",
    "tool_use",
    "constraint_compliance",
    "escalation_quality",
    "efficiency",
)


def _run() -> RunBundle:
    sampled = load_scenario_distribution("E01").sample(50, 42)
    scenarios = tuple(item for item in sampled if item.partition == Partition.SEARCH)
    return asyncio.run(
        run_batch(
            create_e01_runtime,
            create_e01_baseline_policy(),
            scenarios,
            partition=Partition.SEARCH,
            sampling_seed=42,
        )
    )


def test_e01_declares_the_standard_six_dimension_suite() -> None:
    spec = create_e01_runtime().spec
    evaluators = create_e01_evaluators()

    assert tuple(item.id for item in spec.evaluation.dimensions) == DIMENSIONS
    assert tuple(item.dimension for item in spec.evaluation.evaluators) == DIMENSIONS
    assert tuple(item.dimension for item in evaluators) == DIMENSIONS
    assert all(isinstance(item, Evaluator) for item in evaluators)


def test_run_produces_ordered_decomposed_evaluation_vectors() -> None:
    run = _run()
    original_trajectories = tuple(item.model_dump_json() for item in run.trajectories)

    evaluation = evaluate_run(run, create_e01_evaluators())

    assert len(evaluation.vectors) == len(run.trajectories) == 32
    assert tuple(vector.trajectory_id for vector in evaluation.vectors) == tuple(
        trajectory.trajectory_id for trajectory in run.trajectories
    )
    assert all(
        tuple(result.dimension for result in vector.results) == DIMENSIONS
        for vector in evaluation.vectors
    )
    assert all(vector.reward is None for vector in evaluation.vectors)
    assert tuple(item.model_dump_json() for item in run.trajectories) == original_trajectories


def test_e01_baseline_vector_exposes_dimension_specific_behavior() -> None:
    evaluation = evaluate_run(_run(), create_e01_evaluators())
    pass_counts = {
        dimension: sum(
            vector.results[index].passed for vector in evaluation.vectors
        )
        for index, dimension in enumerate(DIMENSIONS)
    }

    assert pass_counts == {
        "task_success": 29,
        "grounding": 32,
        "tool_use": 32,
        "constraint_compliance": 32,
        "escalation_quality": 29,
        "efficiency": 32,
    }


def test_evaluation_records_are_deeply_immutable() -> None:
    vector = evaluate_run(_run(), create_e01_evaluators()).vectors[0]

    with pytest.raises(ValidationError):
        vector.results[0].score = 0.0
    with pytest.raises(TypeError, match="immutable"):
        vector.results[0].evidence["actual_resolution"] = "changed"


def test_evaluation_vector_rejects_duplicate_dimensions() -> None:
    vector = evaluate_run(_run(), create_e01_evaluators()).vectors[0]

    with pytest.raises(ValidationError, match="dimensions must be unique"):
        EvaluationVector(
            trajectory_id=vector.trajectory_id,
            scenario_id=vector.scenario_id,
            results=(vector.results[0], vector.results[0]),
        )


def test_reward_requires_explicit_complete_normalized_weights() -> None:
    vector = evaluate_run(_run(), create_e01_evaluators()).vectors[0]
    weights = {dimension: 1 / len(DIMENSIONS) for dimension in DIMENSIONS}

    reward = aggregate_reward(vector.results, weights)

    assert reward.score == pytest.approx(1.0)
    assert set(reward.weights) == set(DIMENSIONS)
    with pytest.raises(ValueError, match="cover every"):
        aggregate_reward(vector.results, {"task_success": 1.0})
    with pytest.raises(ValidationError, match="sum to 1.0"):
        Reward(score=0.5, weights={dimension: 1.0 for dimension in DIMENSIONS})


@dataclass
class RecordingJudge:
    name: str = "reference-judge"
    case: Any = None
    output: str | None = None

    def score(self, case: Any, output: str) -> float:
        self.case = case
        self.output = output
        return 0.75


def test_legacy_gnomon_judge_adapter_preserves_contract_without_dependency() -> None:
    run = _run()
    judge = RecordingJudge()
    adapter = LegacyGnomonJudgeEvaluator(
        judge=judge,
        case_factory=lambda scenario: {"id": scenario.id},
        dimension="task_success",
        pass_threshold=0.7,
    )

    result = adapter.evaluate(run.trajectories[0], run.scenarios[0])

    assert result.score == 0.75
    assert result.passed is True
    assert result.evaluator.name == "legacy_gnomon:reference-judge"
    assert judge.case == {"id": run.scenarios[0].id}
    assert judge.output is not None
    assert "resolution" in json.loads(judge.output)
    assert isinstance(adapter, Evaluator)


class MisattributedEvaluator:
    name = "bad"
    version = "1.0"
    dimension = "task_success"

    def evaluate(
        self, trajectory: Trajectory, scenario: Scenario
    ) -> EvaluationResult:
        return EvaluationResult(
            trajectory_id="trajectory_0000000000000000",
            scenario_id=scenario.id,
            evaluator=EvaluatorReference(name=self.name, version=self.version),
            dimension=self.dimension,
            score=1.0,
            passed=True,
        )


def test_evaluation_runner_rejects_misattributed_evidence() -> None:
    run = _run()

    with pytest.raises(ValueError, match="incorrectly attributed"):
        evaluate_trajectory(
            run.trajectories[0], run.scenarios[0], (MisattributedEvaluator(),)
        )


def test_evaluation_sidecar_round_trips_without_changing_run(tmp_path: Path) -> None:
    run = _run()
    store = JsonlArtifactStore(tmp_path)
    run_path = store.write(run)
    trajectories_before = (run_path / "trajectories.jsonl").read_bytes()
    evaluation = evaluate_run(run, create_e01_evaluators())

    path = store.write_evaluations(evaluation)
    same_path = store.write_evaluations(evaluation)
    restored = store.read_evaluations(run.manifest.run_id)

    assert path == same_path == run_path / "evaluations.jsonl"
    assert restored == evaluation
    assert len(path.read_text().splitlines()) == 32
    assert (run_path / "trajectories.jsonl").read_bytes() == trajectories_before


def test_evaluation_sidecar_never_overwrites_different_evidence(tmp_path: Path) -> None:
    run = _run()
    store = JsonlArtifactStore(tmp_path)
    store.write(run)
    evaluation = evaluate_run(run, create_e01_evaluators())
    store.write_evaluations(evaluation)
    first = evaluation.vectors[0]
    changed_result = first.results[0].model_copy(update={"score": 0.0, "passed": False})
    changed_vector = first.model_copy(
        update={"results": (changed_result, *first.results[1:])}
    )
    changed = EvaluationBundle(
        run_id=evaluation.run_id,
        evaluators=evaluation.evaluators,
        vectors=(changed_vector, *evaluation.vectors[1:]),
    )

    with pytest.raises(ArtifactStoreError, match="already has different evidence"):
        store.write_evaluations(changed)


def test_environment_yaml_loads_with_all_evaluator_references() -> None:
    spec = load_environment_spec(
        Path("environments/enterprise25/E01_claims_dispute/environment.yaml")
    )

    assert len(spec.evaluation.dimensions) == len(spec.evaluation.evaluators) == 6
