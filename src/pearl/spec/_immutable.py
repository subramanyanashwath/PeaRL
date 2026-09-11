"""Internal helpers for deeply immutable JSON evidence."""

from __future__ import annotations

import json
from typing import Any


class FrozenDict(dict[str, Any]):
    """A recursively frozen, JSON-compatible dictionary snapshot."""

    def __deepcopy__(self, memo: dict[int, Any]) -> FrozenDict:
        return self

    def __setitem__(self, key: str, value: Any) -> None:
        raise TypeError("evidence snapshots are immutable")

    def __delitem__(self, key: str) -> None:
        raise TypeError("evidence snapshots are immutable")

    def clear(self) -> None:
        raise TypeError("evidence snapshots are immutable")

    def pop(self, *args: Any) -> Any:
        raise TypeError("evidence snapshots are immutable")

    def popitem(self) -> tuple[str, Any]:
        raise TypeError("evidence snapshots are immutable")

    def setdefault(self, key: str, default: Any = None) -> Any:
        raise TypeError("evidence snapshots are immutable")

    def update(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError("evidence snapshots are immutable")

    def __ior__(self, value: Any) -> FrozenDict:  # type: ignore[misc, override]
        raise TypeError("evidence snapshots are immutable")


def freeze_json(value: Any) -> Any:
    """Copy a value through strict JSON, then recursively remove mutable containers."""
    try:
        copied = json.loads(json.dumps(value, allow_nan=False))
    except (TypeError, ValueError) as exc:
        raise ValueError("evidence must contain only finite JSON values") from exc
    return _freeze_loaded_json(copied)


def _freeze_loaded_json(value: Any) -> Any:
    if isinstance(value, dict):
        return FrozenDict({key: _freeze_loaded_json(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze_loaded_json(item) for item in value)
    return value
