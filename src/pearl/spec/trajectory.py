"""Immutable execution evidence and Run identity records."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from pearl.spec.scenario import Partition


class FrozenDict(dict[str, Any]):
    """A recursively frozen, JSON-compatible dictionary snapshot."""

    def __deepcopy__(self, memo: dict[int, Any]) -> FrozenDict:
        return self

    def __setitem__(self, key: str, value: Any) -> None:
        raise TypeError("execution snapshots are immutable")

    def __delitem__(self, key: str) -> None:
        raise TypeError("execution snapshots are immutable")

    def clear(self) -> None:
        raise TypeError("execution snapshots are immutable")

    def pop(self, *args: Any) -> Any:
        raise TypeError("execution snapshots are immutable")

    def popitem(self) -> tuple[str, Any]:
        raise TypeError("execution snapshots are immutable")

    def setdefault(self, key: str, default: Any = None) -> Any:
        raise TypeError("execution snapshots are immutable")

    def update(self, *args: Any, **kwargs: Any) -> None:
        raise TypeError("execution snapshots are immutable")

    def __ior__(self, value: Any) -> FrozenDict:  # type: ignore[misc, override]
        raise TypeError("execution snapshots are immutable")


def _freeze_json(value: Any) -> Any:
    """Copy a value through strict JSON, then recursively remove mutable containers."""
    try:
        copied = json.loads(json.dumps(value, allow_nan=False))
    except (TypeError, ValueError) as exc:
        raise ValueError("execution evidence must contain only finite JSON values") from exc
    return _freeze_loaded_json(copied)


def _freeze_loaded_json(value: Any) -> Any:
    if isinstance(value, dict):
        return FrozenDict({key: _freeze_loaded_json(item) for key, item in value.items()})
    if isinstance(value, list):
        return tuple(_freeze_loaded_json(item) for item in value)
    return value


class _EvidenceRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class PolicyReference(_EvidenceRecord):
    """Versioned Policy identity fixed for an Episode or Run."""

    name: str = Field(min_length=1)
    version: str = Field(min_length=1)
    config_hash: str = Field(min_length=64, max_length=64, pattern=r"^[0-9a-f]{64}$")


class Step(_EvidenceRecord):
    """One immutable state-observation-action transition."""

    index: int = Field(ge=0)
    state_before: dict[str, Any]
    observation: dict[str, Any]
    action: dict[str, Any]
    tool_call: dict[str, Any] | None = None
    tool_result: dict[str, Any] | None = None
    state_after: dict[str, Any]
    latency_ms: int = Field(default=0, ge=0)

    @model_validator(mode="after")
    def freeze_snapshots(self) -> Step:
        object.__setattr__(self, "state_before", _freeze_json(self.state_before))
        object.__setattr__(self, "observation", _freeze_json(self.observation))
        object.__setattr__(self, "action", _freeze_json(self.action))
        object.__setattr__(
            self,
            "tool_call",
            None if self.tool_call is None else _freeze_json(self.tool_call),
        )
        object.__setattr__(
            self,
            "tool_result",
            None if self.tool_result is None else _freeze_json(self.tool_result),
        )
        object.__setattr__(self, "state_after", _freeze_json(self.state_after))
        return self


class Trajectory(_EvidenceRecord):
    """Complete immutable execution trace for one Episode."""

    trajectory_id: str = Field(pattern=r"^trajectory_[0-9a-f]{16}$")
    environment_id: str = Field(min_length=1)
    environment_version: int = Field(ge=1)
    scenario_id: str = Field(min_length=1)
    policy: PolicyReference
    steps: tuple[Step, ...] = Field(min_length=1)
    termination_reason: str = Field(min_length=1)
    runtime_metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_trace(self) -> Trajectory:
        for expected_index, step in enumerate(self.steps):
            if step.index != expected_index:
                raise ValueError("Trajectory Step indexes must be contiguous and zero-based")
            if expected_index and self.steps[expected_index - 1].state_after != step.state_before:
                raise ValueError("Each Step must begin from the preceding Step's state_after")
        object.__setattr__(self, "runtime_metadata", _freeze_json(self.runtime_metadata))
        expected_id = trajectory_id_for(
            environment_id=self.environment_id,
            environment_version=self.environment_version,
            scenario_id=self.scenario_id,
            policy=self.policy,
            steps=self.steps,
            termination_reason=self.termination_reason,
            runtime_metadata=self.runtime_metadata,
        )
        if self.trajectory_id != expected_id:
            raise ValueError("trajectory_id does not match immutable execution content")
        return self


class RunManifest(_EvidenceRecord):
    """Fixed execution inputs and ordered Scenario membership for one Run."""

    artifact_schema_version: Literal["1.0"] = "1.0"
    run_id: str = Field(pattern=r"^run_[0-9a-f]{16}$")
    environment_id: str = Field(min_length=1)
    environment_version: int = Field(ge=1)
    partition: Partition
    sampling_seed: int = Field(ge=0)
    scenario_ids: tuple[str, ...] = Field(min_length=1)
    policy: PolicyReference

    @model_validator(mode="after")
    def validate_scenario_ids(self) -> RunManifest:
        if len(set(self.scenario_ids)) != len(self.scenario_ids):
            raise ValueError("RunManifest scenario_ids must be unique")
        return self


EMPTY_POLICY_CONFIG_HASH = hashlib.sha256(b"{}").hexdigest()


def policy_reference(name: str, version: str, config_hash: str | None = None) -> PolicyReference:
    """Build the canonical reference for a Policy with no Day 9 PolicyConfig yet."""
    return PolicyReference(
        name=name,
        version=version,
        config_hash=config_hash or EMPTY_POLICY_CONFIG_HASH,
    )


def trajectory_id_for(
    *,
    environment_id: str,
    environment_version: int,
    scenario_id: str,
    policy: PolicyReference,
    steps: tuple[Step, ...] | list[Step],
    termination_reason: str,
    runtime_metadata: dict[str, Any],
) -> str:
    """Derive a stable Trajectory ID from the complete behavioral evidence."""
    identity = {
        "environment_id": environment_id,
        "environment_version": environment_version,
        "scenario_id": scenario_id,
        "policy": policy,
        "steps": steps,
        "termination_reason": termination_reason,
        "runtime_metadata": runtime_metadata,
    }
    digest = hashlib.sha256(canonical_json_bytes(identity)).hexdigest()[:16]
    return f"trajectory_{digest}"


def canonical_json_bytes(value: Any) -> bytes:
    """Serialize a Pydantic or JSON value for stable content identities."""
    return json.dumps(
        deepcopy(value),
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
        default=_json_default,
    ).encode("utf-8")


def _json_default(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")
