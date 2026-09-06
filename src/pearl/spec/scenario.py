"""Declarative Seed Scenario and generated Scenario models."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, RootModel


class Partition(StrEnum):
    """Statistically distinct evidence partitions."""

    SEARCH = "search"
    VALIDATION = "validation"
    CONFIRMATION = "confirmation"


class State(RootModel[dict[str, Any]]):
    """One concrete environment state."""

    model_config = ConfigDict(frozen=True)


class MutationRecord(BaseModel):
    """Versioned, replayable record of one bounded transformation."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    mutator: str = Field(min_length=1)
    version: str = Field(min_length=1)
    parameters: dict[str, Any] = Field(default_factory=dict)


class SeedScenarioProvenance(BaseModel):
    """Human authorship record for a trusted Seed Scenario."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    author: str = Field(min_length=1)
    notes: str | None = None


class ScenarioProvenance(BaseModel):
    """Inputs required to reproduce a generated Scenario."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    seed_scenario: str | None = None
    environment_version: int | None = Field(default=None, ge=1)
    distribution_version: str | None = None
    mutations: tuple[MutationRecord, ...] = ()


class ScenarioContent(BaseModel):
    """Content shared by authored seeds and generated Scenarios."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    environment_id: str = Field(min_length=1)
    initial_state: State
    persona: dict[str, Any] = Field(default_factory=dict)
    conditions: tuple[str, ...] = ()
    tool_conditions: dict[str, str] = Field(default_factory=dict)
    ground_truth: dict[str, Any] = Field(default_factory=dict)


class SeedScenario(ScenarioContent):
    """A deliberately human-authored trusted reference case."""

    id: str = Field(min_length=1)
    provenance: SeedScenarioProvenance


class Scenario(ScenarioContent):
    """One reproducible instantiated situation from an Environment."""

    id: str = Field(min_length=1)
    seed: int = Field(ge=0)
    partition: Partition = Partition.SEARCH
    provenance: ScenarioProvenance = Field(default_factory=ScenarioProvenance)
