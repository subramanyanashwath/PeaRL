"""Compatibility adapters for pre-PeaRL Judge interfaces."""

from __future__ import annotations

import json
import math
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, Protocol

from pearl.spec import (
    EvaluationResult,
    EvaluatorReference,
    Scenario,
    Trajectory,
)


class LegacyGnomonJudge(Protocol):
    """Structural copy of Gnomon's stable case/output scoring contract."""

    name: str

    def score(self, case: Any, output: str) -> float: ...


LegacyCaseFactory = Callable[[Scenario], Any]
TrajectoryOutputFormatter = Callable[[Trajectory], str]


def _final_state_output(trajectory: Trajectory) -> str:
    return json.dumps(
        trajectory.steps[-1].state_after,
        sort_keys=True,
        separators=(",", ":"),
    )


@dataclass(frozen=True)
class LegacyGnomonJudgeEvaluator:
    """Adapt a synchronous Gnomon Judge without coupling PeaRL core to Gnomon."""

    judge: LegacyGnomonJudge
    case_factory: LegacyCaseFactory
    dimension: str
    version: str = "legacy"
    pass_threshold: float = 0.5
    output_formatter: TrajectoryOutputFormatter = _final_state_output

    def __post_init__(self) -> None:
        if not math.isfinite(self.pass_threshold) or not 0 <= self.pass_threshold <= 1:
            raise ValueError("pass_threshold must be finite and between 0 and 1")

    @property
    def name(self) -> str:
        return f"legacy_gnomon:{self.judge.name}"

    def evaluate(self, trajectory: Trajectory, scenario: Scenario) -> EvaluationResult:
        score = self.judge.score(
            self.case_factory(scenario), self.output_formatter(trajectory)
        )
        if not math.isfinite(score) or not 0 <= score <= 1:
            raise ValueError("Legacy Gnomon Judge score must be finite and between 0 and 1")
        return EvaluationResult(
            trajectory_id=trajectory.trajectory_id,
            scenario_id=scenario.id,
            evaluator=EvaluatorReference(name=self.name, version=self.version),
            dimension=self.dimension,
            score=score,
            passed=score >= self.pass_threshold,
            evidence={
                "adapter": "legacy_gnomon_judge",
                "judge_name": self.judge.name,
                "pass_threshold": self.pass_threshold,
            },
        )
