"""Bootstrapped confidence intervals.

Gnomon's first statistical primitive. A typed, decision-oriented wrapper over
``scipy.stats.bootstrap`` with sensible defaults (95% CI, 10,000 resamples,
percentile method) and a result object that knows how to answer the question
*"does my interval exclude this value?"* — which is the question that actually
matters when you're deciding whether a result is real.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Literal

import numpy as np
from scipy import stats as _stats

BootstrapMethod = Literal["percentile", "basic", "bca"]


@dataclass(frozen=True)
class BootstrapResult:
    """Result of a bootstrap confidence-interval computation.

    Attributes
    ----------
    point_estimate
        The statistic computed on the observed data.
    low, high
        Lower and upper bounds of the confidence interval.
    confidence_level
        The nominal coverage probability (e.g. 0.95).
    n_resamples
        Number of bootstrap resamples used.
    method
        The method used to construct the interval.
    """

    point_estimate: float
    low: float
    high: float
    confidence_level: float
    n_resamples: int
    method: BootstrapMethod

    def __repr__(self) -> str:  # pragma: no cover - cosmetic
        return (
            f"BootstrapResult(point_estimate={self.point_estimate:.4f}, "
            f"ci=[{self.low:.4f}, {self.high:.4f}] @ "
            f"{self.confidence_level:.0%}, "
            f"n_resamples={self.n_resamples}, method='{self.method}')"
        )

    @property
    def width(self) -> float:
        """Width of the interval (``high - low``)."""
        return self.high - self.low

    def excludes(self, value: float) -> bool:
        """Return ``True`` if ``value`` lies outside the confidence interval.

        This is the decision-relevant question: *does the CI exclude the null
        value I care about (typically 0)?* If yes, we have evidence the
        statistic differs from the null. If no, the data are consistent with
        the null.
        """
        return value < self.low or value > self.high


def bootstrap_ci(
    *data: Sequence[float],
    statistic: Callable[..., float],
    n_resamples: int = 10_000,
    confidence_level: float = 0.95,
    method: BootstrapMethod = "percentile",
    paired: bool = True,
    random_state: int | None = None,
) -> BootstrapResult:
    """Compute a bootstrap confidence interval for ``statistic`` of ``data``.

    A thin, typed wrapper over :func:`scipy.stats.bootstrap`. The wrapper exists
    so that statistical results in Gnomon flow through a consistent typed
    object that knows about confidence levels, widths, and decision-relevant
    questions like :meth:`BootstrapResult.excludes`.

    Parameters
    ----------
    *data
        One or more 1-D array-likes of observations. Multiple arrays are
        treated as paired observations and resampled jointly (rows preserved)
        when ``paired=True``.
    statistic
        Function taking the same number of arrays as ``data`` and returning a
        scalar.
    n_resamples
        Number of bootstrap resamples. Default: 10,000.
    confidence_level
        Nominal coverage probability. Default: 0.95.
    method
        Method for constructing the CI from the bootstrap distribution. One of
        ``"percentile"`` (default), ``"basic"``, or ``"bca"``.
    paired
        Whether observations across input arrays are paired. Default: True.
        Set to ``False`` only if you have independent (unpaired) samples.
    random_state
        Seed for reproducibility.

    Returns
    -------
    BootstrapResult

    Raises
    ------
    ValueError
        If no data arrays are provided, or if paired arrays have different
        lengths.

    Examples
    --------
    Bootstrap CI on Spearman correlation between two paired samples:

    >>> import numpy as np
    >>> from scipy import stats
    >>> rng = np.random.default_rng(0)
    >>> x = rng.normal(size=50)
    >>> y = x + 0.1 * rng.normal(size=50)
    >>> result = bootstrap_ci(
    ...     x, y,
    ...     statistic=lambda a, b: stats.spearmanr(a, b).statistic,
    ...     random_state=0,
    ...     n_resamples=2000,
    ... )
    >>> result.excludes(0.0)
    True
    """
    if not data:
        raise ValueError("bootstrap_ci requires at least one data array")

    arrays = [np.asarray(d) for d in data]

    if paired and len({len(a) for a in arrays}) != 1:
        raise ValueError(
            "All input arrays must have the same length when paired=True"
        )

    point_estimate = float(statistic(*arrays))

    res = _stats.bootstrap(
        arrays,
        statistic,
        n_resamples=n_resamples,
        confidence_level=confidence_level,
        method=method,
        paired=paired,
        random_state=random_state,
        vectorized=False,
    )

    return BootstrapResult(
        point_estimate=point_estimate,
        low=float(res.confidence_interval.low),
        high=float(res.confidence_interval.high),
        confidence_level=confidence_level,
        n_resamples=n_resamples,
        method=method,
    )
