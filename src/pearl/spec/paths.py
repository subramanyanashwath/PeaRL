"""Discovery of canonical data in source checkouts and installed distributions."""

from __future__ import annotations

import sysconfig
from importlib.metadata import PackageNotFoundError, distribution
from pathlib import Path


def canonical_data_path(relative: Path) -> Path:
    """Locate one canonical data path without assuming an installation scheme."""
    source_path = Path(__file__).resolve().parents[3] / relative
    if source_path.exists():
        return source_path

    installed_relative = Path("share") / "pearl" / relative
    try:
        installed_path = Path(
            str(distribution("pearl-agent").locate_file(installed_relative))
        )
    except PackageNotFoundError:
        installed_path = None
    if installed_path is not None and installed_path.exists():
        return installed_path

    return Path(sysconfig.get_path("data")) / installed_relative
