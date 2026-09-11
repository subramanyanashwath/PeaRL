"""Metric-aware paired comparisons for replayed PeaRL Runs."""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import Literal

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator

from pearl.gnomon.bootstrap import BootstrapMethod, bootstrap_ci

PairedMetricType = Literal["binary", "continuous_bounded"]


class PairedComparison(BaseModel):
    """A mean metric comparison over aligned Scenario pairs."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    dimension: str = Field(min_length=1)
    metric_type: PairedMetricType
    baseline_estimate: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    candidate_estimate: float = Field(ge=0.0, le=1.0, allow_inf_nan=False)
    paired_delta: float = Field(ge=-1.0, le=1.0, allow_inf_nan=False)
    ci_low: float = Field(ge=-1.0, le=1.0, allow_inf_nan=False)
    ci_high: float = Field(ge=-1.0, le=1.0, allow_inf_nan=False)
    confidence_level: float = Field(gt=0.0, lt=1.0)
    n_pairs: int = Field(ge=2)
    method: Literal["paired_bootstrap_mean_delta"] = "paired_bootstrap_mean_delta"
    bootstrap_method: BootstrapMethod
    n_resamples: int = Field(gt=0)
    random_seed: int

    @model_validator(mode="after")
    def validate_interval(self) -> PairedComparison:
        if self.ci_low > self.ci_high:
            raise ValueError("Paired confidence interval bounds are reversed")
        return self


def paired_metric_comparison(
    baseline: Sequence[float],
    candidate: Sequence[float],
    *,
    dimension: str,
    metric_type: PairedMetricType,
    confidence_level: float = 0.95,
    n_resamples: int = 10_000,
    method: BootstrapMethod = "percentile",
    random_seed: int = 0,
) -> PairedComparison:
    """Compare values whose positions represent the same Scenario IDs."""
    baseline_values = tuple(float(value) for value in baseline)
    candidate_values = tuple(float(value) for value in candidate)
    if len(baseline_values) != len(candidate_values):
        raise ValueError("Paired samples must have the same length")
    if len(baseline_values) < 2:
        raise ValueError("Paired comparison requires at least two Scenario pairs")
    _validate_values(baseline_values, metric_type, "baseline")
    _validate_values(candidate_values, metric_type, "candidate")

    def mean_delta(baseline_array: np.ndarray, candidate_array: np.ndarray) -> float:
        return float(np.mean(candidate_array - baseline_array))

    interval = bootstrap_ci(
        baseline_values,
        candidate_values,
        statistic=mean_delta,
        n_resamples=n_resamples,
        confidence_level=confidence_level,
        method=method,
        paired=True,
        random_state=random_seed,
    )
    baseline_estimate = float(np.mean(baseline_values))
    candidate_estimate = float(np.mean(candidate_values))
    return PairedComparison(
        dimension=dimension,
        metric_type=metric_type,
        baseline_estimate=baseline_estimate,
        candidate_estimate=candidate_estimate,
        paired_delta=candidate_estimate - baseline_estimate,
        ci_low=interval.low,
        ci_high=interval.high,
        confidence_level=confidence_level,
        n_pairs=len(baseline_values),
        bootstrap_method=method,
        n_resamples=n_resamples,
        random_seed=random_seed,
    )


def _validate_values(
    values: tuple[float, ...], metric_type: PairedMetricType, label: str
) -> None:
    if any(not math.isfinite(value) or not 0.0 <= value <= 1.0 for value in values):
        raise ValueError(f"{label} values must be finite and bounded in [0, 1]")
    if metric_type == "binary" and any(value not in (0.0, 1.0) for value in values):
        raise ValueError(f"{label} binary values must be exactly 0 or 1")
