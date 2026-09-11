from __future__ import annotations

import asyncio
from collections.abc import Mapping

import pytest

from pearl.environments.enterprise25 import (
    create_e01_baseline_policy,
    create_e01_evaluators,
    create_e01_runtime,
)
from pearl.evaluators import evaluate_run
from pearl.gnomon import PowerAssessment, compare_evaluated_runs
from pearl.runtime.runner import RunBundle, run_batch, run_id_for
from pearl.scenarios import load_scenario_distribution
from pearl.spec import (
    EvaluationBundle,
    EvaluationVector,
    Partition,
    PolicyReference,
    Trajectory,
)
from pearl.spec.trajectory import trajectory_id_for


def _evaluated_run(
    partition: Partition,
) -> tuple[RunBundle, EvaluationBundle]:
    scenarios = tuple(
        scenario
        for scenario in load_scenario_distribution("E01").sample(50, 42)
        if scenario.partition == partition
    )
    run = asyncio.run(
        run_batch(
            create_e01_runtime,
            create_e01_baseline_policy(),
            scenarios,
            partition=partition,
            sampling_seed=42,
        )
    )
    return run, evaluate_run(run, create_e01_evaluators())


def _candidate_run(
    baseline: RunBundle, *, sampling_seed: int | None = None
) -> RunBundle:
    policy = PolicyReference(
        name="candidate",
        version="1.0",
        config_hash="1" * 64,
    )
    trajectories = tuple(
        Trajectory(
            trajectory_id=trajectory_id_for(
                environment_id=trajectory.environment_id,
                environment_version=trajectory.environment_version,
                scenario_id=trajectory.scenario_id,
                policy=policy,
                steps=trajectory.steps,
                termination_reason=trajectory.termination_reason,
                runtime_metadata=dict(trajectory.runtime_metadata),
            ),
            environment_id=trajectory.environment_id,
            environment_version=trajectory.environment_version,
            scenario_id=trajectory.scenario_id,
            policy=policy,
            steps=trajectory.steps,
            termination_reason=trajectory.termination_reason,
            runtime_metadata=dict(trajectory.runtime_metadata),
        )
        for trajectory in baseline.trajectories
    )
    fixed_sampling_seed = baseline.manifest.sampling_seed
    if sampling_seed is not None:
        fixed_sampling_seed = sampling_seed
    run_id = run_id_for(
        environment_id=baseline.manifest.environment_id,
        environment_version=baseline.manifest.environment_version,
        partition=baseline.manifest.partition,
        sampling_seed=fixed_sampling_seed,
        scenarios=baseline.scenarios,
        policy=policy,
        trajectories=trajectories,
    )
    manifest = baseline.manifest.model_copy(
        update={
            "run_id": run_id,
            "policy": policy,
            "sampling_seed": fixed_sampling_seed,
        }
    )
    return RunBundle(manifest, baseline.scenarios, trajectories)


def _evaluation_for(
    run: RunBundle,
    source: EvaluationBundle,
    overrides: Mapping[str, bool] | None = None,
) -> EvaluationBundle:
    changed = overrides or {}
    vectors: list[EvaluationVector] = []
    for trajectory, source_vector in zip(
        run.trajectories, source.vectors, strict=True
    ):
        results = tuple(
            result.model_copy(
                update={
                    "trajectory_id": trajectory.trajectory_id,
                    "passed": changed.get(result.dimension, result.passed),
                    "score": float(changed.get(result.dimension, result.passed))
                    if result.dimension in changed
                    else result.score,
                }
            )
            for result in source_vector.results
        )
        vectors.append(
            EvaluationVector(
                trajectory_id=trajectory.trajectory_id,
                scenario_id=trajectory.scenario_id,
                results=results,
            )
        )
    return EvaluationBundle(
        run_id=run.manifest.run_id,
        evaluators=source.evaluators,
        vectors=tuple(vectors),
    )


@pytest.fixture(scope="module")
def search_evidence() -> tuple[RunBundle, EvaluationBundle]:
    return _evaluated_run(Partition.SEARCH)


@pytest.fixture(scope="module")
def confirmation_evidence() -> tuple[RunBundle, EvaluationBundle]:
    return _evaluated_run(Partition.CONFIRMATION)


def test_strong_search_result_cannot_ship(
    search_evidence: tuple[RunBundle, EvaluationBundle],
) -> None:
    baseline_run, source = search_evidence
    candidate_run = _candidate_run(baseline_run)
    baseline = _evaluation_for(baseline_run, source, {"task_success": False})
    candidate = _evaluation_for(candidate_run, source, {"task_success": True})

    verdict = compare_evaluated_runs(
        baseline_run,
        baseline,
        candidate_run,
        candidate,
        create_e01_runtime().spec,
        n_resamples=500,
    )

    assert verdict.verdict == "ITERATE"
    assert "Confirmation" in verdict.reason
    assert verdict.power.status == "unavailable"
    assert "independent-arm" in verdict.power.reason


def test_held_out_effect_with_passing_gates_ships(
    confirmation_evidence: tuple[RunBundle, EvaluationBundle],
) -> None:
    baseline_run, source = confirmation_evidence
    candidate_run = _candidate_run(baseline_run)
    baseline = _evaluation_for(baseline_run, source, {"task_success": False})
    candidate = _evaluation_for(candidate_run, source, {"task_success": True})

    verdict = compare_evaluated_runs(
        baseline_run,
        baseline,
        candidate_run,
        candidate,
        create_e01_runtime().spec,
        minimum_effect_size=0.2,
        n_resamples=500,
    )

    assert verdict.verdict == "SHIP"
    assert verdict.partition == Partition.CONFIRMATION
    assert all(gate.passed for gate in verdict.hard_gates)
    primary = next(
        item for item in verdict.comparisons if item.dimension == "task_success"
    )
    assert primary.paired_delta == 1.0
    assert primary.ci_low == 1.0


def test_hard_gate_failure_blocks_metric_improvement(
    confirmation_evidence: tuple[RunBundle, EvaluationBundle],
) -> None:
    baseline_run, source = confirmation_evidence
    candidate_run = _candidate_run(baseline_run)
    baseline = _evaluation_for(baseline_run, source, {"task_success": False})
    candidate = _evaluation_for(
        candidate_run,
        source,
        {"task_success": True, "constraint_compliance": False},
    )

    verdict = compare_evaluated_runs(
        baseline_run,
        baseline,
        candidate_run,
        candidate,
        create_e01_runtime().spec,
        n_resamples=500,
    )

    assert verdict.verdict == "BLOCK"
    assert verdict.hard_gates[0].passed is False
    assert verdict.hard_gates[0].threshold == 1.0


def test_underpowered_is_specific_when_power_evidence_is_supplied(
    search_evidence: tuple[RunBundle, EvaluationBundle],
) -> None:
    baseline_run, source = search_evidence
    candidate_run = _candidate_run(baseline_run)
    candidate = _evaluation_for(candidate_run, source)
    power = PowerAssessment(
        status="underpowered",
        design="paired_binary",
        method="reference_method",
        target_power=0.8,
        achieved_power=0.42,
        reason="Only 32 pairs were available for the prespecified effect.",
    )

    verdict = compare_evaluated_runs(
        baseline_run,
        source,
        candidate_run,
        candidate,
        create_e01_runtime().spec,
        n_resamples=500,
        power=power,
    )

    assert verdict.verdict == "UNDERPOWERED"
    assert verdict.power == power


def test_misaligned_partitions_return_invalid(
    search_evidence: tuple[RunBundle, EvaluationBundle],
    confirmation_evidence: tuple[RunBundle, EvaluationBundle],
) -> None:
    search_run, search_evaluations = search_evidence
    confirmation_run, confirmation_evaluations = confirmation_evidence

    verdict = compare_evaluated_runs(
        search_run,
        search_evaluations,
        confirmation_run,
        confirmation_evaluations,
        create_e01_runtime().spec,
        n_resamples=100,
    )

    assert verdict.verdict == "INVALID"
    assert "partitions" in verdict.reason


def test_misaligned_sampling_seeds_return_invalid(
    search_evidence: tuple[RunBundle, EvaluationBundle],
) -> None:
    baseline_run, baseline_evaluations = search_evidence
    candidate_run = _candidate_run(baseline_run, sampling_seed=43)
    candidate_evaluations = _evaluation_for(candidate_run, baseline_evaluations)

    verdict = compare_evaluated_runs(
        baseline_run,
        baseline_evaluations,
        candidate_run,
        candidate_evaluations,
        create_e01_runtime().spec,
        n_resamples=100,
    )

    assert verdict.verdict == "INVALID"
    assert "sampling seeds" in verdict.reason


def test_invalid_effect_threshold_returns_structured_invalid(
    search_evidence: tuple[RunBundle, EvaluationBundle],
) -> None:
    baseline_run, baseline_evaluations = search_evidence
    candidate_run = _candidate_run(baseline_run)
    candidate_evaluations = _evaluation_for(candidate_run, baseline_evaluations)

    verdict = compare_evaluated_runs(
        baseline_run,
        baseline_evaluations,
        candidate_run,
        candidate_evaluations,
        create_e01_runtime().spec,
        minimum_effect_size=-0.1,
        n_resamples=100,
    )

    assert verdict.verdict == "INVALID"
    assert "minimum_effect_size" in verdict.reason
