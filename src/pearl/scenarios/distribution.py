"""Configured deterministic Scenario distributions."""

from __future__ import annotations

import hashlib
import random
import re
from pathlib import Path
from typing import Annotated, Any, Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from pearl.scenarios.mutators import (
    ChangePersona,
    DropStateField,
    ScenarioMutator,
    SetStateValue,
    SetToolCondition,
)
from pearl.scenarios.partitions import assign_partition
from pearl.spec.loader import SpecLoadError, load_seed_scenario
from pearl.spec.paths import canonical_data_path
from pearl.spec.scenario import Scenario, ScenarioProvenance, SeedScenario


class _Config(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class DropStateFieldConfig(_Config):
    type: Literal["drop_state_field"]
    fields: tuple[str, ...] = Field(min_length=1)
    condition: str = "missing_evidence"
    ground_truth_updates: dict[str, Any] = Field(default_factory=dict)


class SetStateValueConfig(_Config):
    type: Literal["set_state_value"]
    field: str = Field(min_length=1)
    values: tuple[Any, ...] = Field(min_length=1)
    condition: str = "conflicting_truth"
    ground_truth_updates: dict[str, Any] = Field(default_factory=dict)


class SetToolConditionConfig(_Config):
    type: Literal["set_tool_condition"]
    tools: tuple[str, ...] = Field(min_length=1)
    status: str = Field(min_length=1)
    condition: str = "tool_outage"
    ground_truth_updates: dict[str, Any] = Field(default_factory=dict)


class ChangePersonaConfig(_Config):
    type: Literal["change_persona"]
    personas: tuple[dict[str, Any], ...] = Field(min_length=1)
    condition: str = "changed_persona"
    ground_truth_updates: dict[str, Any] = Field(default_factory=dict)


MutatorConfig = Annotated[
    DropStateFieldConfig
    | SetStateValueConfig
    | SetToolConditionConfig
    | ChangePersonaConfig,
    Field(discriminator="type"),
]


class ScenarioDistributionSpec(_Config):
    """Serializable inputs to a deterministic sampling algorithm."""

    pearl_scenario_distribution_version: Literal["1.0"]
    environment_id: str = Field(min_length=1)
    environment_version: int = Field(ge=1)
    version: str = Field(min_length=1)
    min_mutations: int = Field(default=1, ge=0)
    max_mutations: int = Field(default=2, ge=0)
    mutators: tuple[MutatorConfig, ...] = Field(min_length=1)

    @model_validator(mode="after")
    def validate_mutation_bounds(self) -> ScenarioDistributionSpec:
        if self.min_mutations > self.max_mutations:
            raise ValueError("min_mutations cannot exceed max_mutations")
        if self.max_mutations > len(self.mutators):
            raise ValueError("max_mutations cannot exceed the configured mutator count")
        return self


class ScenarioDistribution:
    """A loaded set of Seed Scenarios and bounded generic mutators."""

    def __init__(
        self,
        spec: ScenarioDistributionSpec,
        seeds: tuple[SeedScenario, ...],
    ) -> None:
        if not seeds:
            raise ValueError("A Scenario Distribution requires at least one Seed Scenario.")
        if any(seed.environment_id != spec.environment_id for seed in seeds):
            raise ValueError("All Seed Scenarios must reference the Distribution environment.")
        if len({seed.id for seed in seeds}) != len(seeds):
            raise ValueError("Seed Scenario IDs must be unique within a Distribution.")
        self.spec = spec
        self.seeds = tuple(sorted(seeds, key=lambda item: item.id))
        self.mutators = tuple(_build_mutator(config) for config in spec.mutators)

    def sample(self, n: int, seed: int) -> tuple[Scenario, ...]:
        """Generate ``n`` Scenarios; equal inputs produce byte-equal models."""
        if n < 1:
            raise ValueError("n must be at least 1.")
        if seed < 0:
            raise ValueError("seed must be non-negative.")

        return tuple(self._sample_one(index, seed) for index in range(n))

    def _sample_one(self, index: int, master_seed: int) -> Scenario:
        identity = (
            f"{self.spec.environment_id}|{self.spec.environment_version}|"
            f"{self.spec.version}|{master_seed}|{index}"
        )
        digest = hashlib.sha256(identity.encode("utf-8")).digest()
        scenario_seed = int.from_bytes(digest[:8], "big")
        rng = random.Random(scenario_seed)
        seed_scenario = rng.choice(self.seeds)
        short_id = self.spec.environment_id.rsplit(".", maxsplit=1)[-1]
        scenario_id = f"{short_id}.S{digest.hex()[:12]}"
        scenario = Scenario(
            id=scenario_id,
            environment_id=self.spec.environment_id,
            seed=scenario_seed,
            partition=assign_partition(identity),
            initial_state=seed_scenario.initial_state.model_copy(deep=True),
            persona=dict(seed_scenario.persona),
            conditions=seed_scenario.conditions,
            tool_conditions=dict(seed_scenario.tool_conditions),
            ground_truth=dict(seed_scenario.ground_truth),
            provenance=ScenarioProvenance(
                seed_scenario=seed_scenario.id,
                environment_version=self.spec.environment_version,
                distribution_version=self.spec.version,
            ),
        )

        count = rng.randint(self.spec.min_mutations, self.spec.max_mutations)
        remaining = list(self.mutators)
        for _ in range(count):
            applicable = [mutator for mutator in remaining if mutator.applicable(scenario)]
            if not applicable:
                break
            mutator = rng.choice(applicable)
            scenario = mutator.mutate(scenario, rng)
            remaining.remove(mutator)
        return scenario


def default_environments_path() -> Path:
    """Return the environment data root in a checkout or installed wheel."""
    relative = Path("environments") / "enterprise25"
    return canonical_data_path(relative)


def resolve_environment_path(environment: str, root: str | Path | None = None) -> Path:
    """Resolve ``E01`` or ``enterprise25.E01`` without environment-specific code."""
    short_id = environment.rsplit(".", maxsplit=1)[-1].upper()
    if re.fullmatch(r"E\d{2}", short_id) is None:
        raise SpecLoadError(f'Unknown Environment reference "{environment}".')
    base = Path(root) if root is not None else default_environments_path()
    matches = sorted(path for path in base.glob(f"{short_id}_*") if path.is_dir())
    if len(matches) != 1:
        raise SpecLoadError(f'Could not resolve Environment "{environment}" under "{base}".')
    return matches[0]


def load_scenario_distribution(
    environment: str, root: str | Path | None = None
) -> ScenarioDistribution:
    """Load a configured Distribution and all of its human-authored seeds."""
    environment_path = resolve_environment_path(environment, root)
    config_path = environment_path / "distribution.yaml"
    try:
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError) as exc:
        raise SpecLoadError(f'Could not read Scenario Distribution "{config_path}": {exc}') from exc
    except yaml.YAMLError as exc:
        raise SpecLoadError(
            f'Could not parse Scenario Distribution "{config_path}": {exc}'
        ) from exc
    try:
        spec = ScenarioDistributionSpec.model_validate(payload)
    except ValidationError as exc:
        first = exc.errors()[0]
        location = ".".join(str(part) for part in first["loc"] if part != "function-after")
        raise SpecLoadError(
            f'Scenario Distribution is invalid at field "{location}": {first["msg"]}.'
        ) from exc
    seed_paths = sorted((environment_path / "seeds").glob("*.yaml"))
    seeds = tuple(load_seed_scenario(path) for path in seed_paths)
    try:
        return ScenarioDistribution(spec, seeds)
    except ValueError as exc:
        raise SpecLoadError(str(exc)) from exc


def _build_mutator(config: MutatorConfig) -> ScenarioMutator:
    if isinstance(config, DropStateFieldConfig):
        return DropStateField(
            config.fields, config.condition, config.ground_truth_updates
        )
    if isinstance(config, SetStateValueConfig):
        return SetStateValue(
            config.field, config.values, config.condition, config.ground_truth_updates
        )
    if isinstance(config, SetToolConditionConfig):
        return SetToolCondition(
            config.tools, config.status, config.condition, config.ground_truth_updates
        )
    return ChangePersona(config.personas, config.condition, config.ground_truth_updates)
