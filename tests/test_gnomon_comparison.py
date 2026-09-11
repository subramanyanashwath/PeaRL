from __future__ import annotations

import numpy as np
import pytest
from scipy import stats

from pearl.gnomon import paired_metric_comparison


def test_binary_paired_comparison_matches_scipy_reference() -> None:
    baseline = (0.0, 1.0, 0.0, 1.0, 0.0, 0.0)
    candidate = (1.0, 1.0, 0.0, 1.0, 1.0, 0.0)

    result = paired_metric_comparison(
        baseline,
        candidate,
        dimension="task_success",
        metric_type="binary",
        n_resamples=2_000,
        random_seed=17,
    )
    reference = stats.bootstrap(
        (np.asarray(baseline), np.asarray(candidate)),
        lambda left, right: float(np.mean(right - left)),
        paired=True,
        vectorized=False,
        method="percentile",
        n_resamples=2_000,
        random_state=17,
    )

    assert result.baseline_estimate == pytest.approx(2 / 6)
    assert result.candidate_estimate == pytest.approx(4 / 6)
    assert result.paired_delta == pytest.approx(2 / 6)
    assert result.ci_low == pytest.approx(reference.confidence_interval.low)
    assert result.ci_high == pytest.approx(reference.confidence_interval.high)
    assert result.method == "paired_bootstrap_mean_delta"
    assert result.n_pairs == 6


def test_continuous_comparison_preserves_pairing() -> None:
    result = paired_metric_comparison(
        (0.1, 0.8, 0.4, 0.2),
        (0.2, 0.7, 0.8, 0.2),
        dimension="grounding",
        metric_type="continuous_bounded",
        n_resamples=500,
        random_seed=3,
    )

    assert result.baseline_estimate == pytest.approx(0.375)
    assert result.candidate_estimate == pytest.approx(0.475)
    assert result.paired_delta == pytest.approx(0.1)


def test_metric_contract_rejects_non_binary_values() -> None:
    with pytest.raises(ValueError, match="exactly 0 or 1"):
        paired_metric_comparison(
            (0.0, 0.5),
            (0.0, 1.0),
            dimension="task_success",
            metric_type="binary",
        )


def test_paired_comparison_rejects_misaligned_lengths() -> None:
    with pytest.raises(ValueError, match="same length"):
        paired_metric_comparison(
            (0.0, 1.0),
            (1.0,),
            dimension="task_success",
            metric_type="binary",
        )
