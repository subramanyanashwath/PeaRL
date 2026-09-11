"""Immutable decomposed evaluation evidence."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from pearl.spec._immutable import freeze_json

StandardDimension = Literal[
    "task_success",
    "grounding",
    "tool_use",
    "constraint_compliance",
    "escalation_quality",
    "efficiency",
]


class _EvaluationRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class EvaluatorReference(_EvaluationRecord):
    """Versioned identity for one Evaluator implementation."""

    name: str = Field(min_length=1)
    version: str = Field(min_length=1)


class EvaluationResult(_EvaluationRecord):
    """One normalized measurement of one Trajectory dimension."""

    trajectory_id: str = Field(pattern=r"^trajectory_[0-9a-f]{16}$")
    scenario_id: str = Field(min_length=1)
    evaluator: EvaluatorReference
    dimension: str = Field(min_length=1, pattern=r"^[a-z][a-z0-9_]*$")
    score: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    passed: bool
    evidence: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def freeze_evidence(self) -> EvaluationResult:
        object.__setattr__(self, "evidence", freeze_json(self.evidence))
        return self


class Reward(_EvaluationRecord):
    """Optional explicit scalar aggregation; never a vector replacement."""

    score: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    weights: dict[str, float] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_weights(self) -> Reward:
        if any(not math.isfinite(weight) or weight < 0 for weight in self.weights.values()):
            raise ValueError("Reward weights must be finite and non-negative")
        if not math.isclose(sum(self.weights.values()), 1.0, abs_tol=1e-9):
            raise ValueError("Reward weights must sum to 1.0")
        object.__setattr__(self, "weights", freeze_json(self.weights))
        return self


class EvaluationVector(_EvaluationRecord):
    """Decomposed measurements attached to one immutable Trajectory."""

    trajectory_id: str = Field(pattern=r"^trajectory_[0-9a-f]{16}$")
    scenario_id: str = Field(min_length=1)
    results: tuple[EvaluationResult, ...] = Field(min_length=1)
    reward: Reward | None = None

    @model_validator(mode="after")
    def validate_results(self) -> EvaluationVector:
        dimensions = tuple(result.dimension for result in self.results)
        if len(set(dimensions)) != len(dimensions):
            raise ValueError("EvaluationVector dimensions must be unique")
        for result in self.results:
            if (
                result.trajectory_id != self.trajectory_id
                or result.scenario_id != self.scenario_id
            ):
                raise ValueError("EvaluationResult identity must match its vector")
        if self.reward is not None and set(self.reward.weights) != set(dimensions):
            raise ValueError("Reward weights must cover every vector dimension exactly")
        return self


class EvaluationBundle(_EvaluationRecord):
    """One fixed Evaluator suite applied to every Episode in a Run."""

    evaluation_schema_version: Literal["1.0"] = "1.0"
    run_id: str = Field(pattern=r"^run_[0-9a-f]{16}$")
    evaluators: tuple[EvaluatorReference, ...] = Field(min_length=1)
    vectors: tuple[EvaluationVector, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_suite(self) -> EvaluationBundle:
        names = tuple(evaluator.name for evaluator in self.evaluators)
        if len(set(names)) != len(names):
            raise ValueError("EvaluationBundle Evaluator names must be unique")
        trajectory_ids = tuple(vector.trajectory_id for vector in self.vectors)
        if len(set(trajectory_ids)) != len(trajectory_ids):
            raise ValueError("EvaluationBundle Trajectory IDs must be unique")
        expected = self.evaluators
        for vector in self.vectors:
            actual = tuple(result.evaluator for result in vector.results)
            if actual != expected:
                raise ValueError(
                    "Every EvaluationVector must use the fixed ordered Evaluator suite"
                )
        return self


def aggregate_reward(
    results: Sequence[EvaluationResult], weights: Mapping[str, float]
) -> Reward:
    """Aggregate a complete vector only when explicit weights are supplied."""
    result_by_dimension = {result.dimension: result for result in results}
    if len(result_by_dimension) != len(results):
        raise ValueError("Cannot aggregate duplicate EvaluationResult dimensions")
    if set(weights) != set(result_by_dimension):
        raise ValueError("Reward weights must cover every result dimension exactly")
    reward = Reward(score=0.0, weights=dict(weights))
    score = sum(
        reward.weights[dimension] * result.score
        for dimension, result in result_by_dimension.items()
    )
    return Reward(score=min(1.0, max(0.0, score)), weights=dict(reward.weights))
