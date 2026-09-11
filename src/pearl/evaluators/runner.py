"""Apply one fixed Evaluator suite without mutating execution evidence."""

from __future__ import annotations

from collections.abc import Mapping, Sequence

from pearl.evaluators.base import Evaluator
from pearl.runtime.runner import RunBundle
from pearl.spec import (
    EvaluationBundle,
    EvaluationResult,
    EvaluationVector,
    EvaluatorReference,
    Reward,
    Scenario,
    Trajectory,
    aggregate_reward,
)


def evaluate_trajectory(
    trajectory: Trajectory,
    scenario: Scenario,
    evaluators: Sequence[Evaluator],
    *,
    reward_weights: Mapping[str, float] | None = None,
) -> EvaluationVector:
    """Produce one decomposed vector while enforcing Evaluator attribution."""
    fixed_evaluators = tuple(evaluators)
    _validate_evaluators(fixed_evaluators)
    if trajectory.scenario_id != scenario.id:
        raise ValueError("Trajectory and Scenario IDs must match for evaluation")
    if trajectory.environment_id != scenario.environment_id:
        raise ValueError("Trajectory and Scenario Environments must match for evaluation")

    results: list[EvaluationResult] = []
    for evaluator in fixed_evaluators:
        result = evaluator.evaluate(trajectory, scenario)
        expected_reference = EvaluatorReference(
            name=evaluator.name, version=evaluator.version
        )
        if (
            result.trajectory_id != trajectory.trajectory_id
            or result.scenario_id != scenario.id
            or result.evaluator != expected_reference
            or result.dimension != evaluator.dimension
        ):
            raise ValueError(
                f'Evaluator "{evaluator.name}" returned incorrectly attributed evidence'
            )
        results.append(result)

    reward: Reward | None = None
    if reward_weights is not None:
        reward = aggregate_reward(results, reward_weights)
    return EvaluationVector(
        trajectory_id=trajectory.trajectory_id,
        scenario_id=scenario.id,
        results=tuple(results),
        reward=reward,
    )


def evaluate_run(
    run: RunBundle,
    evaluators: Sequence[Evaluator],
    *,
    reward_weights: Mapping[str, float] | None = None,
) -> EvaluationBundle:
    """Evaluate every Run Episode in manifest order with one fixed suite."""
    fixed_evaluators = tuple(evaluators)
    _validate_evaluators(fixed_evaluators)
    vectors = tuple(
        evaluate_trajectory(
            trajectory,
            scenario,
            fixed_evaluators,
            reward_weights=reward_weights,
        )
        for scenario, trajectory in zip(
            run.scenarios, run.trajectories, strict=True
        )
    )
    references = tuple(
        EvaluatorReference(name=evaluator.name, version=evaluator.version)
        for evaluator in fixed_evaluators
    )
    return EvaluationBundle(
        run_id=run.manifest.run_id,
        evaluators=references,
        vectors=vectors,
    )


def _validate_evaluators(evaluators: tuple[Evaluator, ...]) -> None:
    if not evaluators:
        raise ValueError("Evaluation requires at least one Evaluator")
    names = tuple(evaluator.name for evaluator in evaluators)
    dimensions = tuple(evaluator.dimension for evaluator in evaluators)
    if len(set(names)) != len(names):
        raise ValueError("Evaluator names must be unique within a suite")
    if len(set(dimensions)) != len(dimensions):
        raise ValueError("Evaluator dimensions must be unique within a vector")
