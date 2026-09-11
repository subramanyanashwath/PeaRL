"""Integrated, non-compensatory decisions over paired Run evidence."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from pearl.gnomon.comparison import PairedComparison, paired_metric_comparison
from pearl.runtime.runner import RunBundle, run_id_for
from pearl.spec import EnvironmentSpec, EvaluationBundle, HardGate, Partition

VerdictKind = Literal["SHIP", "ITERATE", "BLOCK", "UNDERPOWERED", "INVALID"]
PowerStatus = Literal["powered", "underpowered", "unavailable"]


class PowerAssessment(BaseModel):
    """Design-specific power status without borrowing an incompatible method."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    status: PowerStatus
    design: str = Field(min_length=1)
    method: str | None = None
    target_power: float | None = Field(default=None, gt=0.0, lt=1.0)
    achieved_power: float | None = Field(default=None, ge=0.0, le=1.0)
    reason: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_status(self) -> PowerAssessment:
        if self.status == "unavailable":
            if any(
                value is not None
                for value in (self.method, self.target_power, self.achieved_power)
            ):
                raise ValueError("Unavailable power cannot claim a method or power value")
            return self
        if (
            self.method is None
            or self.target_power is None
            or self.achieved_power is None
        ):
            raise ValueError("Available power status requires method, target, and achieved power")
        is_powered = self.achieved_power >= self.target_power
        if is_powered != (self.status == "powered"):
            raise ValueError("Power status contradicts achieved versus target power")
        return self


class HardGateAssessment(BaseModel):
    """One deterministic, non-compensatory Hard Gate decision."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    metric: str = Field(min_length=1)
    operator: Literal["gte", "lte", "max_regression"]
    configured_value: float = Field(allow_inf_nan=False)
    baseline_estimate: float = Field(ge=0.0, le=1.0)
    candidate_estimate: float = Field(ge=0.0, le=1.0)
    threshold: float = Field(allow_inf_nan=False)
    passed: bool


class GnomonVerdict(BaseModel):
    """Structured answer to a stated baseline-versus-Candidate hypothesis."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    gnomon_schema_version: Literal["1.0"] = "1.0"
    verdict: VerdictKind
    baseline_run_id: str = Field(min_length=1)
    candidate_run_id: str = Field(min_length=1)
    environment_id: str | None = None
    environment_version: int | None = Field(default=None, ge=1)
    partition: Partition | None = None
    primary_metric: str = Field(min_length=1)
    minimum_effect_size: float = Field(ge=0.0, le=1.0)
    comparisons: tuple[PairedComparison, ...] = ()
    hard_gates: tuple[HardGateAssessment, ...] = ()
    power: PowerAssessment
    reason: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_decision(self) -> GnomonVerdict:
        if self.verdict == "INVALID":
            if self.comparisons or self.hard_gates:
                raise ValueError("INVALID verdict cannot retain inferential results")
            return self
        if (
            self.environment_id is None
            or self.environment_version is None
            or self.partition is None
            or not self.comparisons
        ):
            raise ValueError("A valid verdict requires Environment and comparison evidence")
        if self.verdict == "SHIP" and (
            self.partition != Partition.CONFIRMATION
            or any(not gate.passed for gate in self.hard_gates)
        ):
            raise ValueError("SHIP requires Confirmation evidence and passing Hard Gates")
        if self.verdict == "UNDERPOWERED" and self.power.status != "underpowered":
            raise ValueError("UNDERPOWERED requires an underpowered design assessment")
        return self


def paired_power_unavailable() -> PowerAssessment:
    """Return the honest Day 7 power status for paired replay."""
    return PowerAssessment(
        status="unavailable",
        design="paired_replay",
        reason=(
            "Power calculation unavailable for this paired design; Gnomon's "
            "independent-arm proportion functions are not applicable."
        ),
    )


def invalid_verdict(
    baseline_run_id: str,
    candidate_run_id: str,
    reason: str,
    *,
    primary_metric: str = "task_success",
    minimum_effect_size: float = 0.0,
) -> GnomonVerdict:
    """Represent broken or misaligned evidence as a specific INVALID decision."""
    return GnomonVerdict(
        verdict="INVALID",
        baseline_run_id=baseline_run_id,
        candidate_run_id=candidate_run_id,
        primary_metric=primary_metric,
        minimum_effect_size=minimum_effect_size,
        power=paired_power_unavailable(),
        reason=reason,
    )


def compare_evaluated_runs(
    baseline_run: RunBundle,
    baseline_evaluations: EvaluationBundle,
    candidate_run: RunBundle,
    candidate_evaluations: EvaluationBundle,
    environment: EnvironmentSpec,
    *,
    primary_metric: str = "task_success",
    minimum_effect_size: float = 0.0,
    confidence_level: float = 0.95,
    n_resamples: int = 10_000,
    random_seed: int = 0,
    power: PowerAssessment | None = None,
) -> GnomonVerdict:
    """Validate, pair, compare, gate, and decide two immutable Runs."""
    if not 0.0 <= minimum_effect_size <= 1.0:
        return invalid_verdict(
            baseline_run.manifest.run_id,
            candidate_run.manifest.run_id,
            "minimum_effect_size must be in [0, 1]",
            primary_metric=primary_metric,
        )
    unavailable = power or paired_power_unavailable()
    try:
        _validate_experiment(
            baseline_run,
            baseline_evaluations,
            candidate_run,
            candidate_evaluations,
            environment,
            primary_metric,
        )
        comparisons = _compare_dimensions(
            baseline_evaluations,
            candidate_evaluations,
            environment,
            confidence_level=confidence_level,
            n_resamples=n_resamples,
            random_seed=random_seed,
        )
        gates = tuple(
            _assess_gate(gate, comparisons) for gate in environment.evaluation.hard_gates
        )
    except ValueError as exc:
        return invalid_verdict(
            baseline_run.manifest.run_id,
            candidate_run.manifest.run_id,
            str(exc),
            primary_metric=primary_metric,
            minimum_effect_size=minimum_effect_size,
        )

    primary = next(item for item in comparisons if item.dimension == primary_metric)
    verdict, reason = _decide(
        primary,
        gates,
        candidate_run.manifest.partition,
        minimum_effect_size,
        unavailable,
    )
    return GnomonVerdict(
        verdict=verdict,
        baseline_run_id=baseline_run.manifest.run_id,
        candidate_run_id=candidate_run.manifest.run_id,
        environment_id=baseline_run.manifest.environment_id,
        environment_version=baseline_run.manifest.environment_version,
        partition=baseline_run.manifest.partition,
        primary_metric=primary_metric,
        minimum_effect_size=minimum_effect_size,
        comparisons=comparisons,
        hard_gates=gates,
        power=unavailable,
        reason=reason,
    )


def _validate_experiment(
    baseline_run: RunBundle,
    baseline_evaluations: EvaluationBundle,
    candidate_run: RunBundle,
    candidate_evaluations: EvaluationBundle,
    environment: EnvironmentSpec,
    primary_metric: str,
) -> None:
    baseline_manifest = baseline_run.manifest
    candidate_manifest = candidate_run.manifest
    _validate_run_evidence(baseline_run, baseline_evaluations, "Baseline")
    _validate_run_evidence(candidate_run, candidate_evaluations, "Candidate")
    if baseline_evaluations.run_id != baseline_manifest.run_id:
        raise ValueError("Baseline evaluations do not belong to the baseline Run")
    if candidate_evaluations.run_id != candidate_manifest.run_id:
        raise ValueError("Candidate evaluations do not belong to the Candidate Run")
    if (
        baseline_manifest.environment_id != candidate_manifest.environment_id
        or baseline_manifest.environment_version != candidate_manifest.environment_version
    ):
        raise ValueError("Runs use different Environment identities or versions")
    if (
        environment.metadata.id != baseline_manifest.environment_id
        or environment.metadata.version != baseline_manifest.environment_version
    ):
        raise ValueError("EnvironmentSpec does not match the compared Runs")
    if baseline_manifest.partition != candidate_manifest.partition:
        raise ValueError("Runs use different evidence partitions")
    if baseline_manifest.sampling_seed != candidate_manifest.sampling_seed:
        raise ValueError("Runs use different Scenario sampling seeds")
    if baseline_manifest.scenario_ids != candidate_manifest.scenario_ids:
        raise ValueError("Runs are not paired by the same ordered Scenario IDs")
    if baseline_run.scenarios != candidate_run.scenarios:
        raise ValueError("Runs contain different Scenario evidence despite matching IDs")
    if baseline_evaluations.evaluators != candidate_evaluations.evaluators:
        raise ValueError("Runs use different Evaluator names or versions")
    baseline_dimensions = tuple(
        result.dimension for result in baseline_evaluations.vectors[0].results
    )
    candidate_dimensions = tuple(
        result.dimension for result in candidate_evaluations.vectors[0].results
    )
    if baseline_dimensions != candidate_dimensions:
        raise ValueError("Runs contain different Evaluation Vector dimensions")
    if primary_metric not in baseline_dimensions:
        raise ValueError(f'Primary metric "{primary_metric}" is absent from the vectors')


def _validate_run_evidence(
    run: RunBundle, evaluations: EvaluationBundle, label: str
) -> None:
    manifest = run.manifest
    scenario_ids = tuple(scenario.id for scenario in run.scenarios)
    trajectory_ids = tuple(trajectory.trajectory_id for trajectory in run.trajectories)
    if scenario_ids != manifest.scenario_ids:
        raise ValueError(f"{label} Scenario records do not match its manifest")
    if tuple(trajectory.scenario_id for trajectory in run.trajectories) != scenario_ids:
        raise ValueError(f"{label} Trajectories do not match its Scenarios")
    if tuple(vector.scenario_id for vector in evaluations.vectors) != scenario_ids:
        raise ValueError(f"{label} Evaluation Vectors do not match its Scenarios")
    if tuple(vector.trajectory_id for vector in evaluations.vectors) != trajectory_ids:
        raise ValueError(f"{label} Evaluation Vectors do not match its Trajectories")
    expected_run_id = run_id_for(
        environment_id=manifest.environment_id,
        environment_version=manifest.environment_version,
        partition=manifest.partition,
        sampling_seed=manifest.sampling_seed,
        scenarios=run.scenarios,
        policy=manifest.policy,
        trajectories=run.trajectories,
    )
    if manifest.run_id != expected_run_id:
        raise ValueError(f"{label} Run identity does not match its evidence")


def _compare_dimensions(
    baseline: EvaluationBundle,
    candidate: EvaluationBundle,
    environment: EnvironmentSpec,
    *,
    confidence_level: float,
    n_resamples: int,
    random_seed: int,
) -> tuple[PairedComparison, ...]:
    dimension_specs = {item.id: item for item in environment.evaluation.dimensions}
    dimensions = tuple(result.dimension for result in baseline.vectors[0].results)
    results: list[PairedComparison] = []
    for index, dimension in enumerate(dimensions):
        try:
            declared_type = dimension_specs[dimension].metric_type
        except KeyError as exc:
            raise ValueError(
                f'Evaluation dimension "{dimension}" is absent from EnvironmentSpec'
            ) from exc
        if declared_type not in ("binary", "continuous"):
            raise ValueError(
                f'Paired comparison does not support metric type "{declared_type}"'
            )
        if declared_type == "binary":
            baseline_values = tuple(
                float(vector.results[index].passed) for vector in baseline.vectors
            )
            candidate_values = tuple(
                float(vector.results[index].passed) for vector in candidate.vectors
            )
            metric_type: Literal["binary", "continuous_bounded"] = "binary"
        else:
            baseline_values = tuple(
                vector.results[index].score for vector in baseline.vectors
            )
            candidate_values = tuple(
                vector.results[index].score for vector in candidate.vectors
            )
            metric_type = "continuous_bounded"
        results.append(
            paired_metric_comparison(
                baseline_values,
                candidate_values,
                dimension=dimension,
                metric_type=metric_type,
                confidence_level=confidence_level,
                n_resamples=n_resamples,
                random_seed=random_seed + index,
            )
        )
    return tuple(results)


def _assess_gate(
    gate: HardGate, comparisons: tuple[PairedComparison, ...]
) -> HardGateAssessment:
    try:
        comparison = next(item for item in comparisons if item.dimension == gate.metric)
    except StopIteration as exc:
        raise ValueError(f'Hard Gate metric "{gate.metric}" was not compared') from exc
    if gate.operator == "gte":
        threshold = gate.value
        passed = comparison.candidate_estimate >= threshold
    elif gate.operator == "lte":
        threshold = gate.value
        passed = comparison.candidate_estimate <= threshold
    else:
        threshold = comparison.baseline_estimate - gate.value
        passed = comparison.candidate_estimate >= threshold
    return HardGateAssessment(
        metric=gate.metric,
        operator=gate.operator,
        configured_value=gate.value,
        baseline_estimate=comparison.baseline_estimate,
        candidate_estimate=comparison.candidate_estimate,
        threshold=threshold,
        passed=passed,
    )


def _decide(
    primary: PairedComparison,
    gates: tuple[HardGateAssessment, ...],
    partition: Partition,
    minimum_effect_size: float,
    power: PowerAssessment,
) -> tuple[VerdictKind, str]:
    failed_gates = tuple(gate.metric for gate in gates if not gate.passed)
    if failed_gates:
        return "BLOCK", f"Hard Gate failed: {', '.join(failed_gates)}."
    if primary.ci_high < -minimum_effect_size:
        return "BLOCK", "The primary metric shows a material paired regression."
    effect_established = primary.ci_low > minimum_effect_size
    if effect_established and partition == Partition.CONFIRMATION:
        return (
            "SHIP",
            "Held-out paired evidence clears the minimum effect and every Hard Gate.",
        )
    if effect_established:
        return (
            "ITERATE",
            "The effect is supported, but SHIP requires held-out Confirmation evidence.",
        )
    if power.status == "underpowered":
        return "UNDERPOWERED", power.reason
    if power.status == "unavailable":
        return (
            "ITERATE",
            "The paired interval does not clear the adoption threshold; "
            "paired-design power is unavailable.",
        )
    return "ITERATE", "The paired interval does not clear the adoption threshold."
