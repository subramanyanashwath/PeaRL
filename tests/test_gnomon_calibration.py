from __future__ import annotations

import pytest
from scipy import stats

from pearl.gnomon import (
    bucketed_agreement,
    calibrate_judge,
    cohen_kappa,
    krippendorff_alpha,
    spearman_correlation,
)


def test_cohen_kappa_matches_hand_calculated_reference() -> None:
    reference = (0, 0, 0, 0, 1, 1, 1, 1, 1, 1)
    judged = (0, 0, 0, 1, 0, 1, 1, 1, 1, 1)

    assert cohen_kappa(reference, judged) == pytest.approx(7 / 12)


def test_krippendorff_nominal_alpha_matches_coincidence_reference() -> None:
    reference = (0, 0, 0, 0, 1, 1, 1, 1, 1, 1)
    judged = (0, 0, 0, 1, 0, 1, 1, 1, 1, 1)

    assert krippendorff_alpha(reference, judged) == pytest.approx(0.6041666667)


def test_krippendorff_interval_alpha_uses_squared_distance() -> None:
    reference = (0.0, 0.25, 0.5, 0.75, 1.0)
    judged = (0.0, 0.2, 0.55, 0.7, 0.9)

    alpha = krippendorff_alpha(reference, judged, level="interval")

    assert 0.95 < alpha <= 1.0


def test_spearman_matches_scipy_reference() -> None:
    reference = (0.1, 0.4, 0.2, 0.9, 0.7)
    judged = (0.2, 0.5, 0.1, 0.8, 0.6)

    assert spearman_correlation(reference, judged) == pytest.approx(
        stats.spearmanr(reference, judged).statistic
    )


def test_bucketed_agreement_reports_empty_and_supported_buckets() -> None:
    result = bucketed_agreement(
        (0.05, 0.15, 0.45, 0.95),
        (0.10, 0.25, 0.42, 1.0),
        buckets=5,
    )

    assert tuple(item.support for item in result) == (2, 0, 1, 0, 1)
    assert result[0].agreement == 0.5
    assert result[1].agreement is None
    assert result[2].agreement == 1.0
    assert result[4].agreement == 1.0


def test_calibration_answers_effect_resolution_question() -> None:
    reference = (0.05, 0.25, 0.45, 0.65, 0.85)
    judged = (0.06, 0.24, 0.46, 0.64, 0.86)

    report = calibrate_judge(
        reference,
        judged,
        minimum_effect_size=0.05,
        n_resamples=500,
        random_seed=5,
    )

    assert report.cohen_kappa == 1.0
    assert report.krippendorff_alpha == 1.0
    assert report.spearman_correlation == pytest.approx(1.0)
    assert report.mean_absolute_error == pytest.approx(0.01)
    assert report.error_ci_high < report.minimum_effect_size
    assert report.reliable_for_effect_size is True
    assert "Calibration passes" in report.reason


def test_calibration_rejects_undefined_rank_evidence() -> None:
    with pytest.raises(ValueError, match="undefined"):
        calibrate_judge(
            (0.5, 0.5, 0.5),
            (0.5, 0.5, 0.5),
            minimum_effect_size=0.1,
            n_resamples=100,
        )
    with pytest.raises(ValueError, match="undefined for constant"):
        spearman_correlation((0.5, 0.5, 0.5), (0.5, 0.5, 0.5))


def test_chance_corrected_agreement_rejects_degenerate_labels() -> None:
    with pytest.raises(ValueError, match="expected agreement is 1"):
        cohen_kappa(("same", "same"), ("same", "same"))
    with pytest.raises(ValueError, match="expected disagreement"):
        krippendorff_alpha(("same", "same"), ("same", "same"))
