import pearl


def test_version() -> None:
    assert pearl.__version__ == "0.1.0.dev0"


def test_gnomon_public_imports() -> None:
    from pearl.gnomon import (
        BootstrapResult,
        BucketAgreement,
        GnomonVerdict,
        HardGateAssessment,
        JudgeCalibrationReport,
        PairedComparison,
        PowerAssessment,
        PowerResult,
        bootstrap_ci,
        bucketed_agreement,
        calibrate_judge,
        cohen_kappa,
        cohens_h,
        compare_evaluated_runs,
        invalid_verdict,
        krippendorff_alpha,
        paired_metric_comparison,
        paired_power_unavailable,
        power_one_proportion,
        power_two_proportions,
        required_n_one_proportion,
        required_n_two_proportions,
        spearman_correlation,
    )

    assert all(
        item is not None
        for item in (
            BootstrapResult,
            BucketAgreement,
            GnomonVerdict,
            HardGateAssessment,
            JudgeCalibrationReport,
            PairedComparison,
            PowerAssessment,
            PowerResult,
            bootstrap_ci,
            bucketed_agreement,
            calibrate_judge,
            cohen_kappa,
            cohens_h,
            compare_evaluated_runs,
            invalid_verdict,
            krippendorff_alpha,
            paired_metric_comparison,
            paired_power_unavailable,
            power_one_proportion,
            power_two_proportions,
            required_n_one_proportion,
            required_n_two_proportions,
            spearman_correlation,
        )
    )
