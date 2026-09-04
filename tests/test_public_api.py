import pearl


def test_version() -> None:
    assert pearl.__version__ == "0.1.0.dev0"


def test_gnomon_public_imports() -> None:
    from pearl.gnomon import (
        BootstrapResult,
        PowerResult,
        bootstrap_ci,
        cohens_h,
        power_one_proportion,
        power_two_proportions,
        required_n_one_proportion,
        required_n_two_proportions,
    )

    assert all(
        item is not None
        for item in (
            BootstrapResult,
            PowerResult,
            bootstrap_ci,
            cohens_h,
            power_one_proportion,
            power_two_proportions,
            required_n_one_proportion,
            required_n_two_proportions,
        )
    )
