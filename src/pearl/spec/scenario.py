"""Concrete Scenario model used by an EnvironmentSpec."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, RootModel


class State(RootModel[dict[str, Any]]):
    """One concrete environment state."""

    model_config = ConfigDict(frozen=True)


class ScenarioProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    seed_scenario: str | None = None
    mutations: tuple[str, ...] = ()


class Scenario(BaseModel):
    """One instantiated situation from an Environment."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(min_length=1)
    environment_id: str = Field(min_length=1)
    seed: int = Field(ge=0)
    initial_state: State
    persona: dict[str, Any] = Field(default_factory=dict)
    conditions: tuple[str, ...] = ()
    tool_conditions: dict[str, str] = Field(default_factory=dict)
    ground_truth: dict[str, Any] = Field(default_factory=dict)
    provenance: ScenarioProvenance = Field(default_factory=ScenarioProvenance)
