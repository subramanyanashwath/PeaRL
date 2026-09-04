"""Tests for gnomon.stats.bootstrap.

Property-based tests against scipy.stats.bootstrap as the reference
implementation, plus decision-oriented tests that verify the wrapper makes
the right calls on the kind of question Gnomon exists to answer:
*does the CI exclude the null value?*
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from scipy import stats

from pearl.gnomon import BootstrapResult, bootstrap_ci


def test_repr_is_readable() -> None:
    rng = np.random.default_rng(0)
    res = bootstrap_ci(
        rng.normal(size=50), statistic=np.mean, random_state=0, n_resamples=500
    )
    text = repr(res)
    assert "BootstrapResult" in text
    assert "ci=" in text
    assert "95%" in text


def test_width_property() -> None:
    res = BootstrapResult(
        point_estimate=0.5,
        low=0.2,
        high=0.8,
        confidence_level=0.95,
        n_resamples=1000,
        method="percentile",
    )
    assert math.isclose(res.width, 0.6)


def test_excludes_boundary_behavior() -> None:
    res = BootstrapResult(
        point_estimate=0.0,
        low=-0.1,
        high=0.1,
        confidence_level=0.95,
        n_resamples=1000,
        method="percentile",
    )
    assert not res.excludes(0.0)
    assert not res.excludes(-0.1)
    assert not res.excludes(0.1)
    assert res.excludes(-0.2)
    assert res.excludes(0.2)


def test_bootstrap_ci_mean_contains_true_value() -> None:
    """A 95% CI on the mean should contain the true mean for a well-powered sample."""
    rng = np.random.default_rng(42)
    x = rng.normal(loc=5.0, scale=1.0, size=200)
    result = bootstrap_ci(
        x, statistic=np.mean, random_state=42, n_resamples=2000
    )
    assert result.low < 5.0 < result.high


def test_bootstrap_ci_excludes_zero_for_strong_correlation() -> None:
    """Spearman r CI on near-perfectly correlated data should exclude zero."""
    rng = np.random.default_rng(0)
    x = rng.normal(size=80)
    y = x + 0.05 * rng.normal(size=80)
    result = bootstrap_ci(
        x,
        y,
        statistic=lambda a, b: stats.spearmanr(a, b).statistic,
        random_state=0,
        n_resamples=2000,
    )
    assert result.excludes(0.0)
    assert result.point_estimate > 0.9


def test_bootstrap_ci_includes_zero_for_independent_data() -> None:
    """Spearman r CI on independent samples should fail to exclude zero."""
    rng = np.random.default_rng(1)
    x = rng.normal(size=30)
    y = rng.normal(size=30)
    result = bootstrap_ci(
        x,
        y,
        statistic=lambda a, b: stats.spearmanr(a, b).statistic,
        random_state=1,
        n_resamples=2000,
    )
    assert not result.excludes(0.0)


def test_bootstrap_ci_matches_scipy_directly() -> None:
    """Property test: output should match a direct scipy.stats.bootstrap call."""
    rng = np.random.default_rng(99)
    x = rng.exponential(scale=2.0, size=100)

    ours = bootstrap_ci(
        x, statistic=np.median, random_state=42, n_resamples=2000
    )
    direct = stats.bootstrap(
        [x],
        np.median,
        n_resamples=2000,
        confidence_level=0.95,
        method="percentile",
        paired=True,
        random_state=42,
        vectorized=False,
    )
    assert math.isclose(ours.low, float(direct.confidence_interval.low))
    assert math.isclose(ours.high, float(direct.confidence_interval.high))
    assert ours.n_resamples == 2000
    assert ours.method == "percentile"


def test_bootstrap_ci_paired_data_matches_scipy() -> None:
    """Property test with paired correlation matches scipy directly."""
    rng = np.random.default_rng(7)
    x = rng.normal(size=60)
    y = 0.4 * x + rng.normal(size=60)

    def spearman(a: np.ndarray, b: np.ndarray) -> float:
        return float(stats.spearmanr(a, b).statistic)

    ours = bootstrap_ci(
        x, y, statistic=spearman, random_state=7, n_resamples=2000
    )
    direct = stats.bootstrap(
        [x, y],
        spearman,
        n_resamples=2000,
        confidence_level=0.95,
        method="percentile",
        paired=True,
        random_state=7,
        vectorized=False,
    )
    assert math.isclose(ours.low, float(direct.confidence_interval.low))
    assert math.isclose(ours.high, float(direct.confidence_interval.high))


def test_no_data_raises() -> None:
    with pytest.raises(ValueError, match="at least one"):
        bootstrap_ci(statistic=np.mean)


def test_mismatched_lengths_raises_when_paired() -> None:
    with pytest.raises(ValueError, match="same length"):
        bootstrap_ci(
            [1, 2, 3],
            [4, 5, 6, 7],
            statistic=lambda a, b: float(np.corrcoef(a, b)[0, 1]),
            random_state=0,
            n_resamples=500,
        )


def test_confidence_level_90_narrower_than_95() -> None:
    """A 90% CI should be narrower than a 95% CI on the same data."""
    rng = np.random.default_rng(2)
    x = rng.normal(size=100)
    ci_90 = bootstrap_ci(
        x,
        statistic=np.mean,
        confidence_level=0.90,
        random_state=2,
        n_resamples=2000,
    )
    ci_95 = bootstrap_ci(
        x,
        statistic=np.mean,
        confidence_level=0.95,
        random_state=2,
        n_resamples=2000,
    )
    assert ci_90.width < ci_95.width
