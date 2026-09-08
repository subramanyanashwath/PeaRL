"""Immutable values exchanged across the EnvironmentRuntime boundary."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from pearl.spec import State


class _RuntimeValue(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Action(_RuntimeValue):
    """One executable action selected by a Policy."""

    id: str = Field(min_length=1)
    arguments: dict[str, Any] = Field(default_factory=dict)


class Observation(_RuntimeValue):
    """One named, policy-visible projection of runtime state."""

    id: str = Field(min_length=1)
    data: dict[str, Any] = Field(default_factory=dict)
    available_actions: tuple[str, ...] = ()


class RuntimeContext(_RuntimeValue):
    """Scenario context available to environment callbacks, excluding Ground Truth."""

    environment_id: str = Field(min_length=1)
    environment_version: int = Field(ge=1)
    scenario_id: str = Field(min_length=1)
    scenario_seed: int = Field(ge=0)
    step_index: int = Field(ge=0)
    persona: dict[str, Any] = Field(default_factory=dict)
    conditions: tuple[str, ...] = ()
    tool_conditions: dict[str, str] = Field(default_factory=dict)


class StateTransition(_RuntimeValue):
    """Pure transition callback output before runtime lifecycle enforcement."""

    state: State
    termination_reason: str | None = None
    tool_call: dict[str, Any] | None = None
    tool_result: dict[str, Any] | None = None
    info: dict[str, Any] = Field(default_factory=dict)


class StepResult(_RuntimeValue):
    """Result of one accepted runtime action."""

    step_index: int = Field(ge=0)
    observation: Observation
    state: State
    terminated: bool
    termination_reason: str | None = None
    tool_call: dict[str, Any] | None = None
    tool_result: dict[str, Any] | None = None
    info: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_termination(self) -> StepResult:
        if self.terminated != (self.termination_reason is not None):
            raise ValueError(
                "terminated must be true exactly when termination_reason is present"
            )
        return self
