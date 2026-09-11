"""Generic wrapper for deterministic, environment-owned evaluation functions."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any

from pearl.spec import (
    EvaluationResult,
    EvaluatorReference,
    Scenario,
    Trajectory,
)


@dataclass(frozen=True)
class EvaluationOutcome:
    """Unattached deterministic score returned by environment evaluation logic."""

    score: float
    passed: bool
    evidence: Mapping[str, Any] = field(default_factory=dict)


EvaluationFunction = Callable[[Trajectory, Scenario], EvaluationOutcome]


@dataclass(frozen=True)
class DeterministicEvaluator:
    """Bind a named dimension to a pure deterministic scoring function."""

    name: str
    version: str
    dimension: str
    function: EvaluationFunction

    def evaluate(self, trajectory: Trajectory, scenario: Scenario) -> EvaluationResult:
        outcome = self.function(trajectory, scenario)
        return EvaluationResult(
            trajectory_id=trajectory.trajectory_id,
            scenario_id=scenario.id,
            evaluator=EvaluatorReference(name=self.name, version=self.version),
            dimension=self.dimension,
            score=outcome.score,
            passed=outcome.passed,
            evidence=dict(outcome.evidence),
        )
