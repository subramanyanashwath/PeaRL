"""Gnomon statistical inference primitives inside PeaRL.

The bootstrap and power modules were migrated from the MIT-licensed Gnomon
project with their tested API semantics and result dataclasses preserved.
"""

from pearl.gnomon.bootstrap import BootstrapResult, bootstrap_ci
from pearl.gnomon.calibration import (
    BucketAgreement,
    JudgeCalibrationReport,
    bucketed_agreement,
    calibrate_judge,
    cohen_kappa,
    krippendorff_alpha,
    spearman_correlation,
)
from pearl.gnomon.comparison import PairedComparison, paired_metric_comparison
from pearl.gnomon.power import (
    PowerResult,
    cohens_h,
    power_one_proportion,
    power_two_proportions,
    required_n_one_proportion,
    required_n_two_proportions,
)
from pearl.gnomon.verdict import (
    GnomonVerdict,
    HardGateAssessment,
    PowerAssessment,
    compare_evaluated_runs,
    invalid_verdict,
    paired_power_unavailable,
)

__all__ = [
    "BootstrapResult",
    "BucketAgreement",
    "GnomonVerdict",
    "HardGateAssessment",
    "JudgeCalibrationReport",
    "PairedComparison",
    "PowerAssessment",
    "PowerResult",
    "bootstrap_ci",
    "bucketed_agreement",
    "calibrate_judge",
    "cohen_kappa",
    "cohens_h",
    "compare_evaluated_runs",
    "invalid_verdict",
    "krippendorff_alpha",
    "paired_metric_comparison",
    "paired_power_unavailable",
    "power_one_proportion",
    "power_two_proportions",
    "required_n_one_proportion",
    "required_n_two_proportions",
    "spearman_correlation",
]
