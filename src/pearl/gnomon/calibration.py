"""Reference-grounded calibration metrics for automated Judges."""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Hashable, Sequence
from typing import Any, Literal, TypeVar, cast

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, model_validator
from scipy import stats as _stats

from pearl.gnomon.bootstrap import bootstrap_ci

ReliabilityLevel = Literal["nominal", "interval"]
RatingT = TypeVar("RatingT")


class BucketAgreement(BaseModel):
    """Agreement within one reference-score bucket."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    low: float = Field(ge=0.0, le=1.0)
    high: float = Field(ge=0.0, le=1.0)
    support: int = Field(ge=0)
    agreement: float | None = Field(default=None, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def validate_bucket(self) -> BucketAgreement:
        if self.low >= self.high:
            raise ValueError("Bucket bounds must be increasing")
        if (self.support == 0) != (self.agreement is None):
            raise ValueError("Agreement must be absent exactly when a bucket is empty")
        return self


class JudgeCalibrationReport(BaseModel):
    """Calibration evidence and an explicit effect-resolution decision."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    n_pairs: int = Field(ge=2)
    buckets: int = Field(ge=2)
    cohen_kappa: float = Field(allow_inf_nan=False)
    krippendorff_alpha: float = Field(allow_inf_nan=False)
    spearman_correlation: float = Field(ge=-1.0, le=1.0, allow_inf_nan=False)
    bucketed_agreement: tuple[BucketAgreement, ...]
    mean_absolute_error: float = Field(ge=0.0, le=1.0)
    error_ci_low: float = Field(ge=0.0, le=1.0)
    error_ci_high: float = Field(ge=0.0, le=1.0)
    minimum_effect_size: float = Field(gt=0.0, le=1.0)
    reliability_floor: float = Field(ge=0.0, le=1.0)
    reliable_for_effect_size: bool
    reason: str = Field(min_length=1)

    @model_validator(mode="after")
    def validate_report(self) -> JudgeCalibrationReport:
        if len(self.bucketed_agreement) != self.buckets:
            raise ValueError("Calibration report must contain every declared bucket")
        if self.error_ci_low > self.error_ci_high:
            raise ValueError("Calibration error interval bounds are reversed")
        return self


def cohen_kappa(reference: Sequence[Hashable], judged: Sequence[Hashable]) -> float:
    """Cohen's kappa for two complete categorical rating sequences."""
    reference_values, judged_values = _validate_pairs(reference, judged)
    total = len(reference_values)
    observed = sum(
        reference_value == judged_value
        for reference_value, judged_value in zip(
            reference_values, judged_values, strict=True
        )
    ) / total
    reference_counts = Counter(reference_values)
    judged_counts = Counter(judged_values)
    labels = set(reference_counts) | set(judged_counts)
    expected = sum(
        (reference_counts[label] / total) * (judged_counts[label] / total)
        for label in labels
    )
    if math.isclose(expected, 1.0):
        raise ValueError("Cohen's kappa is undefined when expected agreement is 1")
    return (observed - expected) / (1.0 - expected)


def krippendorff_alpha(
    reference: Sequence[Hashable | float],
    judged: Sequence[Hashable | float],
    *,
    level: ReliabilityLevel = "nominal",
) -> float:
    """Krippendorff's alpha for two complete coders at nominal or interval level."""
    reference_values, judged_values = _validate_pairs(reference, judged)

    def distance(left: Hashable | float, right: Hashable | float) -> float:
        if level == "nominal":
            return float(left != right)
        try:
            return (float(cast(Any, left)) - float(cast(Any, right))) ** 2
        except (TypeError, ValueError) as exc:
            raise ValueError("Interval alpha requires numeric ratings") from exc

    observed = math.fsum(
        distance(left, right)
        for left, right in zip(reference_values, judged_values, strict=True)
    ) / len(reference_values)
    pooled = (*reference_values, *judged_values)
    expected = math.fsum(
        distance(left, right)
        for index, left in enumerate(pooled)
        for other_index, right in enumerate(pooled)
        if index != other_index
    ) / (len(pooled) * (len(pooled) - 1))
    if math.isclose(expected, 0.0):
        raise ValueError("Krippendorff's alpha is undefined without expected disagreement")
    return 1.0 - observed / expected


def spearman_correlation(reference: Sequence[float], judged: Sequence[float]) -> float:
    """Spearman rank correlation, rejecting undefined constant inputs."""
    reference_values, judged_values = _validate_numeric_pairs(reference, judged)
    if len(set(reference_values)) == 1 or len(set(judged_values)) == 1:
        raise ValueError("Spearman correlation is undefined for constant ratings")
    result = float(_stats.spearmanr(reference_values, judged_values).statistic)
    if not math.isfinite(result):
        raise ValueError("Spearman correlation is undefined for constant ratings")
    return result


def bucketed_agreement(
    reference: Sequence[float], judged: Sequence[float], *, buckets: int = 5
) -> tuple[BucketAgreement, ...]:
    """Report same-bucket agreement conditional on each reference-score bucket."""
    if buckets < 2:
        raise ValueError("buckets must be at least 2")
    reference_values, judged_values = _validate_numeric_pairs(reference, judged)
    _validate_unit_interval(reference_values, "reference")
    _validate_unit_interval(judged_values, "judged")
    reference_bins = tuple(_bucket_index(value, buckets) for value in reference_values)
    judged_bins = tuple(_bucket_index(value, buckets) for value in judged_values)
    results: list[BucketAgreement] = []
    for index in range(buckets):
        members = tuple(
            position
            for position, reference_bin in enumerate(reference_bins)
            if reference_bin == index
        )
        matching = sum(judged_bins[position] == index for position in members)
        results.append(
            BucketAgreement(
                low=index / buckets,
                high=(index + 1) / buckets,
                support=len(members),
                agreement=None if not members else matching / len(members),
            )
        )
    return tuple(results)


def calibrate_judge(
    reference: Sequence[float],
    judged: Sequence[float],
    *,
    minimum_effect_size: float,
    buckets: int = 5,
    reliability_floor: float = 0.8,
    confidence_level: float = 0.95,
    n_resamples: int = 10_000,
    random_seed: int = 0,
) -> JudgeCalibrationReport:
    """Assess whether Judge error is bounded below a stated effect size."""
    if not 0.0 < minimum_effect_size <= 1.0:
        raise ValueError("minimum_effect_size must be in (0, 1]")
    if buckets < 2:
        raise ValueError("buckets must be at least 2")
    if not 0.0 <= reliability_floor <= 1.0:
        raise ValueError("reliability_floor must be in [0, 1]")
    reference_values, judged_values = _validate_numeric_pairs(reference, judged)
    _validate_unit_interval(reference_values, "reference")
    _validate_unit_interval(judged_values, "judged")
    reference_bins = tuple(_bucket_index(value, buckets) for value in reference_values)
    judged_bins = tuple(_bucket_index(value, buckets) for value in judged_values)
    kappa = cohen_kappa(reference_bins, judged_bins)
    alpha = krippendorff_alpha(reference_bins, judged_bins, level="nominal")
    correlation = spearman_correlation(reference_values, judged_values)

    def mean_absolute_error(
        reference_array: np.ndarray, judged_array: np.ndarray
    ) -> float:
        return float(np.mean(np.abs(reference_array - judged_array)))

    error = bootstrap_ci(
        reference_values,
        judged_values,
        statistic=mean_absolute_error,
        confidence_level=confidence_level,
        n_resamples=n_resamples,
        method="percentile",
        paired=True,
        random_state=random_seed,
    )
    reliable = (
        kappa >= reliability_floor
        and alpha >= reliability_floor
        and correlation >= reliability_floor
        and error.high < minimum_effect_size
    )
    if reliable:
        reason = (
            "Calibration passes: reliability metrics meet the stated floor and "
            "the upper confidence bound on Judge error is below the interpreted effect."
        )
    else:
        reason = (
            "Calibration fails: reliability or the uncertainty bound on Judge error "
            "cannot resolve the interpreted effect."
        )
    return JudgeCalibrationReport(
        n_pairs=len(reference_values),
        buckets=buckets,
        cohen_kappa=kappa,
        krippendorff_alpha=alpha,
        spearman_correlation=correlation,
        bucketed_agreement=bucketed_agreement(
            reference_values, judged_values, buckets=buckets
        ),
        mean_absolute_error=error.point_estimate,
        error_ci_low=error.low,
        error_ci_high=error.high,
        minimum_effect_size=minimum_effect_size,
        reliability_floor=reliability_floor,
        reliable_for_effect_size=reliable,
        reason=reason,
    )


def _validate_pairs(
    reference: Sequence[RatingT], judged: Sequence[RatingT]
) -> tuple[tuple[RatingT, ...], tuple[RatingT, ...]]:
    reference_values = tuple(reference)
    judged_values = tuple(judged)
    if len(reference_values) != len(judged_values):
        raise ValueError("Reference and Judge ratings must have the same length")
    if len(reference_values) < 2:
        raise ValueError("Calibration requires at least two rating pairs")
    return reference_values, judged_values


def _validate_numeric_pairs(
    reference: Sequence[float], judged: Sequence[float]
) -> tuple[tuple[float, ...], tuple[float, ...]]:
    paired = _validate_pairs(reference, judged)
    try:
        reference_values = tuple(float(value) for value in paired[0])
        judged_values = tuple(float(value) for value in paired[1])
    except (TypeError, ValueError) as exc:
        raise ValueError("Ratings must be numeric") from exc
    if any(not math.isfinite(value) for value in (*reference_values, *judged_values)):
        raise ValueError("Ratings must be finite")
    return reference_values, judged_values


def _validate_unit_interval(values: tuple[float, ...], label: str) -> None:
    if any(not 0.0 <= value <= 1.0 for value in values):
        raise ValueError(f"{label} ratings must be bounded in [0, 1]")


def _bucket_index(value: float, buckets: int) -> int:
    return min(int(value * buckets), buckets - 1)
