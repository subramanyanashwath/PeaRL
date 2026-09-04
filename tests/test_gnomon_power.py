"""Tests for gnomon.stats.power.

Reference implementations, per the repo's statistical-correctness rule:

1. **R ``pwr`` golden values** — hard-coded outputs of ``pwr.p.test`` and
   ``pwr.2p.test`` for canonical inputs (Cohen's h conventions).
2. **Independent scipy reconstruction** — the tests rebuild the closed-form
   normal-approximation solution directly from ``scipy.stats.norm.ppf``,
   without importing anything from ``gnomon.stats.power`` internals.

Plus round-trip consistency (required_n -> achieved power >= target) and
monotonicity properties.
"""

from __future__ import annotations

import math

import pytest
from scipy import stats

from pearl.gnomon import (
    cohens_h,
    power_one_proportion,
    power_two_proportions,
    required_n_one_proportion,
    required_n_two_proportions,
)


def reference_n(h: float, alpha: float, power: float, two_sided: bool, arms: int) -> float:
    """Closed-form reference built independently from scipy quantiles."""
    z_a = stats.norm.ppf(1 - alpha / 2 if two_sided else 1 - alpha)
    z_b = stats.norm.ppf(power)
    return arms * ((z_a + z_b) / abs(h)) ** 2


# --- Cohen's h -------------------------------------------------------------


def test_cohens_h_known_value() -> None:
    """h(0.5, 0.4) = 2*asin(sqrt(0.5)) - 2*asin(sqrt(0.4)) ~ 0.2014."""
    expected = 2 * math.asin(math.sqrt(0.5)) - 2 * math.asin(math.sqrt(0.4))
    assert math.isclose(cohens_h(0.5, 0.4), expected)
    assert math.isclose(cohens_h(0.5, 0.4), 0.2013579, abs_tol=1e-6)


def test_cohens_h_antisymmetric() -> None:
    assert math.isclose(cohens_h(0.7, 0.3), -cohens_h(0.3, 0.7))


def test_cohens_h_zero_for_equal_proportions() -> None:
    assert cohens_h(0.42, 0.42) == 0.0


def test_cohens_h_rejects_out_of_range() -> None:
    with pytest.raises(ValueError, match="p1"):
        cohens_h(1.2, 0.5)
    with pytest.raises(ValueError, match="p2"):
        cohens_h(0.5, -0.1)


# --- Golden values from R pwr ----------------------------------------------


def test_one_proportion_matches_r_pwr() -> None:
    """R: pwr.p.test(h=0.2, sig.level=0.05, power=0.8) -> n = 196.2215.

    Engineered so cohens_h(p, threshold) == 0.2 exactly by inverting the
    arcsine transform.
    """
    threshold = 0.5
    p = math.sin(math.asin(math.sqrt(threshold)) + 0.2 / 2) ** 2
    assert math.isclose(cohens_h(p, threshold), 0.2)

    result = required_n_one_proportion(p, threshold)
    assert math.isclose(result.n_exact, 196.2215, abs_tol=0.01)
    assert result.n_required == 197


def test_two_proportions_matches_r_pwr() -> None:
    """R: pwr.2p.test(h=0.2, sig.level=0.05, power=0.8) -> n = 392.443 per arm."""
    p2 = 0.5
    p1 = math.sin(math.asin(math.sqrt(p2)) + 0.2 / 2) ** 2

    result = required_n_two_proportions(p1, p2)
    assert math.isclose(result.n_exact, 392.443, abs_tol=0.01)
    assert result.n_required == 393


# --- Property: matches independent scipy reconstruction ---------------------


@pytest.mark.parametrize("p,threshold", [(0.6, 0.5), (0.75, 0.8), (0.55, 0.5), (0.3, 0.5)])
@pytest.mark.parametrize("alpha,power", [(0.05, 0.80), (0.01, 0.90), (0.10, 0.70)])
def test_one_proportion_matches_reference(
    p: float, threshold: float, alpha: float, power: float
) -> None:
    result = required_n_one_proportion(p, threshold, alpha=alpha, power=power)
    expected = reference_n(cohens_h(p, threshold), alpha, power, two_sided=True, arms=1)
    assert math.isclose(result.n_exact, expected, rel_tol=1e-12)
    assert result.n_required == math.ceil(expected)


@pytest.mark.parametrize("p1,p2", [(0.5, 0.6), (0.8, 0.85), (0.4, 0.6)])
@pytest.mark.parametrize("two_sided", [True, False])
def test_two_proportions_matches_reference(p1: float, p2: float, two_sided: bool) -> None:
    result = required_n_two_proportions(p1, p2, two_sided=two_sided)
    expected = reference_n(cohens_h(p1, p2), 0.05, 0.80, two_sided=two_sided, arms=2)
    assert math.isclose(result.n_exact, expected, rel_tol=1e-12)


# --- Round-trip: required n achieves the target power ------------------------


@pytest.mark.parametrize("p,threshold,power", [(0.6, 0.5, 0.8), (0.55, 0.5, 0.9)])
def test_one_proportion_round_trip(p: float, threshold: float, power: float) -> None:
    result = required_n_one_proportion(p, threshold, power=power)
    achieved = power_one_proportion(result.n_required, p, threshold)
    assert achieved >= power
    # Well below the recommendation, power should fall short of target.
    assert power_one_proportion(result.n_required // 2, p, threshold) < power


def test_two_proportions_round_trip() -> None:
    result = required_n_two_proportions(0.5, 0.6)
    achieved = power_two_proportions(result.n_required, 0.5, 0.6)
    assert achieved >= 0.80
    assert power_two_proportions(result.n_required // 2, 0.5, 0.6) < 0.80


# --- Monotonicity properties -------------------------------------------------


def test_higher_power_needs_more_samples() -> None:
    n80 = required_n_two_proportions(0.5, 0.6, power=0.80).n_exact
    n90 = required_n_two_proportions(0.5, 0.6, power=0.90).n_exact
    assert n90 > n80


def test_smaller_alpha_needs_more_samples() -> None:
    n05 = required_n_two_proportions(0.5, 0.6, alpha=0.05).n_exact
    n01 = required_n_two_proportions(0.5, 0.6, alpha=0.01).n_exact
    assert n01 > n05


def test_larger_effect_needs_fewer_samples() -> None:
    small = required_n_one_proportion(0.55, 0.5).n_exact
    large = required_n_one_proportion(0.70, 0.5).n_exact
    assert large < small


def test_one_sided_needs_fewer_samples() -> None:
    two = required_n_one_proportion(0.6, 0.5, two_sided=True).n_exact
    one = required_n_one_proportion(0.6, 0.5, two_sided=False).n_exact
    assert one < two


def test_power_increases_with_n() -> None:
    powers = [power_one_proportion(n, 0.6, 0.5) for n in (25, 50, 100, 200, 400)]
    assert powers == sorted(powers)
    assert powers[-1] > 0.95


# --- Decision-oriented behavior ----------------------------------------------


def test_is_powered() -> None:
    result = required_n_one_proportion(0.6, 0.5)  # n_required = 194
    assert result.is_powered(194)
    assert result.is_powered(500)
    assert not result.is_powered(193)
    assert not result.is_powered(50)


def test_m2_live_run_is_underpowered_for_small_effects() -> None:
    """The M2 live run (n=50 vs a 0.5 bar) is only powered for large effects.

    This is the tool telling on our own eval: 50 cases cannot reliably
    resolve a true pass rate of 0.6 against a 0.5 bar.
    """
    result = required_n_one_proportion(0.6, 0.5)
    assert not result.is_powered(50)
    # But a large effect (0.8 vs 0.5) is comfortably detectable at n=50.
    assert required_n_one_proportion(0.8, 0.5).is_powered(50)


# --- Validation ---------------------------------------------------------------


def test_zero_effect_raises() -> None:
    with pytest.raises(ValueError, match="effect size is zero"):
        required_n_one_proportion(0.5, 0.5)


def test_bad_alpha_raises() -> None:
    with pytest.raises(ValueError, match="alpha"):
        required_n_one_proportion(0.6, 0.5, alpha=1.5)


def test_bad_power_raises() -> None:
    with pytest.raises(ValueError, match="power"):
        required_n_one_proportion(0.6, 0.5, power=0.0)


def test_power_not_exceeding_alpha_raises() -> None:
    with pytest.raises(ValueError, match="must exceed alpha"):
        required_n_one_proportion(0.6, 0.5, alpha=0.5, power=0.3)


def test_nonpositive_n_raises() -> None:
    with pytest.raises(ValueError, match="positive"):
        power_one_proportion(0, 0.6, 0.5)
    with pytest.raises(ValueError, match="positive"):
        power_two_proportions(-5, 0.5, 0.6)
