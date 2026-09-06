"""Stable evidence partition assignment."""

from __future__ import annotations

import hashlib

from pearl.spec.scenario import Partition


def assign_partition(identity: str) -> Partition:
    """Assign 60/20/20 without depending on sample order or batch size."""
    bucket = int.from_bytes(hashlib.sha256(identity.encode("utf-8")).digest()[:8], "big") % 100
    if bucket < 60:
        return Partition.SEARCH
    if bucket < 80:
        return Partition.VALIDATION
    return Partition.CONFIRMATION
