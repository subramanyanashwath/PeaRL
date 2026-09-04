"""Gnomon statistical inference primitives inside PeaRL.

The bootstrap and power modules were migrated from the MIT-licensed Gnomon
project with their tested API semantics and result dataclasses preserved.
"""

from pearl.gnomon.bootstrap import BootstrapResult, bootstrap_ci
from pearl.gnomon.power import (
    PowerResult,
    cohens_h,
    power_one_proportion,
    power_two_proportions,
    required_n_one_proportion,
    required_n_two_proportions,
)

__all__ = [
    "BootstrapResult",
    "PowerResult",
    "bootstrap_ci",
    "cohens_h",
    "power_one_proportion",
    "power_two_proportions",
    "required_n_one_proportion",
    "required_n_two_proportions",
]
