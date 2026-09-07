"""Canonical asynchronous Policy interface."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel, ConfigDict, Field

from pearl.runtime import Action, Observation


class PolicyError(RuntimeError):
    """A Policy could not select a valid action."""


class PolicyContext(BaseModel):
    """Execution metadata available to a Policy, excluding Ground Truth."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    environment_id: str = Field(min_length=1)
    environment_version: int = Field(ge=1)
    scenario_id: str = Field(min_length=1)
    step_index: int = Field(ge=0)
    metadata: dict[str, Any] = Field(default_factory=dict)


@runtime_checkable
class Policy(Protocol):
    """The complete agent system being evaluated."""

    @property
    def name(self) -> str: ...

    @property
    def version(self) -> str: ...

    async def act(self, observation: Observation, context: PolicyContext) -> Action: ...
