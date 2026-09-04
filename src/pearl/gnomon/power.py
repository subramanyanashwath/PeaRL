"""Power analysis for pass-rate evals.

Answers the question you should ask *before* spending money on an eval run:
*how many cases do I need to detect the effect I care about?* — and its
retrospective twin: *was my run big enough to trust?*

Two designs are covered, matching how evals are actually compared:

- **one proportion vs. a bar** — is the pass rate above a fixed threshold?
  (the shape of a single-model ship gate)
- **two proportions** — is model B's pass rate different from model A's?
  (the shape of an A/B comparison; one ``n`` per arm)

Effect sizes use Cohen's *h* (arcsine-transformed difference of proportions)
with the standard normal approximation — the same convention as R's ``pwr``
package (``pwr.p.test`` / ``pwr.2p.test``), which serves as the reference
implementation for the tests.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal

from scipy import stats as _stats

PowerKind = Literal["one_proportion", "two_proportions"]


@dataclass(frozen=True)
class PowerResult:
    """Result of a sample-size computation.

    Attributes
    ----------
    n_required
        Recommended sample size, rounded up. For ``two_proportions`` this is
        the size of *each* arm, not the total.
    n_exact
        The unrounded solution of the power equation.
    effect_size
        Cohen's h for the specified proportions.
    alpha
        Type-I error rate the design controls.
    power
        Target probability of detecting the effect if it is real.
    two_sided
        Whether the test is two-sided.
    kind
        Which design the recommendation is for.
    """

    n_required: int
    n_exact: float
    effect_size: float
    alpha: float
    power: float
    two_sided: bool
    kind: PowerKind

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        per_arm = " per arm" if self.kind == "two_proportions" else ""
        return (
            f"PowerResult(n_required={self.n_required}{per_arm}, "
            f"h={self.effect_size:.4f}, alpha={self.alpha}, "
            f"power={self.power}, kind='{self.kind}')"
        )

    def is_powered(self, n_available: int) -> bool:
        """Return ``True`` if ``n_available`` cases meet the recommendation.

        This is the decision-relevant question: *given the eval set I already
        have, am I powered for the effect I claim to care about?* If not, an
        observed null is UNDERPOWERED, not evidence of no effect.
        """
        return n_available >= self.n_required


def cohens_h(p1: float, p2: float) -> float:
    """Cohen's h effect size between two proportions.

    ``h = 2*asin(sqrt(p1)) - 2*asin(sqrt(p2))``. The arcsine transform makes
    the sampling variance of a proportion approximately independent of its
    true value, so one effect-size scale works across the whole [0, 1] range.
    Conventional anchors: 0.2 small, 0.5 medium, 0.8 large.
    """
    for name, p in (("p1", p1), ("p2", p2)):
        if not 0.0 <= p <= 1.0:
            raise ValueError(f"{name} must be in [0, 1], got {p}")
    return 2 * math.asin(math.sqrt(p1)) - 2 * math.asin(math.sqrt(p2))


def _validate_alpha(alpha: float) -> None:
    if not 0.0 < alpha < 1.0:
        raise ValueError(f"alpha must be in (0, 1), got {alpha}")


def _validate(alpha: float, power: float) -> None:
    _validate_alpha(alpha)
    if not 0.0 < power < 1.0:
        raise ValueError(f"power must be in (0, 1), got {power}")
    if power <= alpha:
        raise ValueError(
            f"power ({power}) must exceed alpha ({alpha}) for the design to be solvable"
        )


def _z_alpha(alpha: float, two_sided: bool) -> float:
    return float(_stats.norm.ppf(1 - alpha / 2 if two_sided else 1 - alpha))


def _solve_n(
    h: float, alpha: float, power: float, two_sided: bool, arms: int
) -> tuple[int, float]:
    """Solve the normal-approximation power equation for n.

    ``power = Phi(|h| * sqrt(n / arms) - z_alpha)`` rearranged for ``n``.
    ``arms`` is 1 for the one-sample design (Var(h_hat) ~ 1/n) and 2 for the
    two-sample equal-n design (Var(h_hat) ~ 2/n).
    """
    if h == 0.0:
        raise ValueError(
            "effect size is zero: the two proportions are equal, so no finite "
            "sample size can detect the difference"
        )
    z_a = _z_alpha(alpha, two_sided)
    z_b = float(_stats.norm.ppf(power))
    n_exact = arms * ((z_a + z_b) / abs(h)) ** 2
    return math.ceil(n_exact), n_exact


def required_n_one_proportion(
    p: float,
    threshold: float,
    *,
    alpha: float = 0.05,
    power: float = 0.80,
    two_sided: bool = True,
) -> PowerResult:
    """Sample size to detect that a pass rate ``p`` differs from ``threshold``.

    Use before a single-model eval against a ship bar: if you believe the true
    pass rate is ``p`` and the bar is ``threshold``, this is how many cases
    you need for the run to have a ``power`` chance of resolving the question
    at significance ``alpha``.

    Matches R's ``pwr.p.test(h=cohens_h(p, threshold), sig.level=alpha,
    power=power)``.

    Examples
    --------
    >>> result = required_n_one_proportion(0.6, 0.5)
    >>> result.n_required
    194
    >>> result.is_powered(50)
    False
    """
    _validate(alpha, power)
    h = cohens_h(p, threshold)
    n_required, n_exact = _solve_n(h, alpha, power, two_sided, arms=1)
    return PowerResult(
        n_required=n_required,
        n_exact=n_exact,
        effect_size=h,
        alpha=alpha,
        power=power,
        two_sided=two_sided,
        kind="one_proportion",
    )


def required_n_two_proportions(
    p1: float,
    p2: float,
    *,
    alpha: float = 0.05,
    power: float = 0.80,
    two_sided: bool = True,
) -> PowerResult:
    """Per-arm sample size to detect a pass-rate difference between two models.

    Use before an A/B eval: if model A's true pass rate is ``p1`` and you care
    about detecting a change to ``p2``, this is how many cases *each* arm
    needs for the comparison to have a ``power`` chance of resolving at
    significance ``alpha``.

    Matches R's ``pwr.2p.test(h=cohens_h(p1, p2), sig.level=alpha,
    power=power)``.

    Examples
    --------
    >>> result = required_n_two_proportions(0.5, 0.6)
    >>> result.n_required
    388
    """
    _validate(alpha, power)
    h = cohens_h(p1, p2)
    n_required, n_exact = _solve_n(h, alpha, power, two_sided, arms=2)
    return PowerResult(
        n_required=n_required,
        n_exact=n_exact,
        effect_size=h,
        alpha=alpha,
        power=power,
        two_sided=two_sided,
        kind="two_proportions",
    )


def power_one_proportion(
    n: int,
    p: float,
    threshold: float,
    *,
    alpha: float = 0.05,
    two_sided: bool = True,
) -> float:
    """Achieved power of an ``n``-case eval of pass rate ``p`` against ``threshold``.

    The retrospective question: *the run is done (or the eval set is fixed) —
    what was the probability it would detect this effect if real?* Below ~0.8,
    a null result is better read as UNDERPOWERED than as evidence of no effect.
    """
    _validate_alpha(alpha)
    if n <= 0:
        raise ValueError(f"n must be positive, got {n}")
    return _power(cohens_h(p, threshold), n, alpha, two_sided, arms=1)


def power_two_proportions(
    n_per_arm: int,
    p1: float,
    p2: float,
    *,
    alpha: float = 0.05,
    two_sided: bool = True,
) -> float:
    """Achieved power of an A/B eval with ``n_per_arm`` cases per arm."""
    _validate_alpha(alpha)
    if n_per_arm <= 0:
        raise ValueError(f"n_per_arm must be positive, got {n_per_arm}")
    return _power(cohens_h(p1, p2), n_per_arm, alpha, two_sided, arms=2)


def _power(h: float, n: int, alpha: float, two_sided: bool, arms: int) -> float:
    z_a = _z_alpha(alpha, two_sided)
    shift = abs(h) * math.sqrt(n / arms)
    power = float(_stats.norm.cdf(shift - z_a))
    if two_sided:
        # Rejection region in the opposite tail; negligible unless h ~ 0.
        power += float(_stats.norm.cdf(-shift - z_a))
    return power
