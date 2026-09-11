"""Canonical synchronous Evaluator interface."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from pearl.spec import EvaluationResult, Scenario, Trajectory


@runtime_checkable
class Evaluator(Protocol):
    """A versioned measurement function over one Trajectory and Scenario."""

    @property
    def name(self) -> str: ...

    @property
    def version(self) -> str: ...

    @property
    def dimension(self) -> str: ...

    def evaluate(
        self, trajectory: Trajectory, scenario: Scenario
    ) -> EvaluationResult: ...
