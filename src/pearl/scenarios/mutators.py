"""Generic, bounded Scenario mutators."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from dataclasses import field as dataclass_field
from random import Random
from typing import Any, ClassVar, Protocol, runtime_checkable

from pearl.spec.scenario import MutationRecord, Scenario, State


@runtime_checkable
class ScenarioMutator(Protocol):
    """A versioned bounded transformation over one Scenario."""

    id: ClassVar[str]
    version: ClassVar[str]

    def applicable(self, scenario: Scenario) -> bool: ...

    def mutate(self, scenario: Scenario, rng: Random) -> Scenario: ...


def _finish(
    scenario: Scenario,
    *,
    mutator: ScenarioMutator,
    parameters: Mapping[str, Any],
    condition: str,
    initial_state: dict[str, Any] | None = None,
    persona: dict[str, Any] | None = None,
    tool_conditions: dict[str, str] | None = None,
    ground_truth_updates: Mapping[str, Any],
) -> Scenario:
    truth = deepcopy(scenario.ground_truth)
    truth.update(deepcopy(dict(ground_truth_updates)))
    provenance = scenario.provenance.model_copy(
        update={
            "mutations": (
                *scenario.provenance.mutations,
                MutationRecord(
                    mutator=mutator.id,
                    version=mutator.version,
                    parameters=deepcopy(dict(parameters)),
                ),
            )
        }
    )
    return scenario.model_copy(
        update={
            "initial_state": State(
                deepcopy(scenario.initial_state.root if initial_state is None else initial_state)
            ),
            "persona": deepcopy(scenario.persona if persona is None else persona),
            "conditions": (*scenario.conditions, condition),
            "tool_conditions": deepcopy(
                scenario.tool_conditions if tool_conditions is None else tool_conditions
            ),
            "ground_truth": truth,
            "provenance": provenance,
        }
    )


@dataclass(frozen=True)
class DropStateField:
    """Remove one present state field, modelling missing evidence."""

    fields: Sequence[str]
    condition: str = "missing_evidence"
    ground_truth_updates: Mapping[str, Any] = dataclass_field(default_factory=dict)
    id: ClassVar[str] = "drop_state_field"
    version: ClassVar[str] = "1.0"

    def applicable(self, scenario: Scenario) -> bool:
        return any(field in scenario.initial_state.root for field in self.fields)

    def mutate(self, scenario: Scenario, rng: Random) -> Scenario:
        candidates = [field for field in self.fields if field in scenario.initial_state.root]
        if not candidates:
            raise ValueError(f"{self.id} is not applicable to Scenario {scenario.id}.")
        field = rng.choice(candidates)
        state = deepcopy(scenario.initial_state.root)
        del state[field]
        return _finish(
            scenario,
            mutator=self,
            parameters={"field": field},
            condition=self.condition,
            initial_state=state,
            ground_truth_updates=self.ground_truth_updates,
        )


@dataclass(frozen=True)
class SetStateValue:
    """Set one state field to a configured conflicting or stale value."""

    field: str
    values: Sequence[Any]
    condition: str = "conflicting_truth"
    ground_truth_updates: Mapping[str, Any] = dataclass_field(default_factory=dict)
    id: ClassVar[str] = "set_state_value"
    version: ClassVar[str] = "1.0"

    def applicable(self, scenario: Scenario) -> bool:
        current = scenario.initial_state.root.get(self.field)
        return self.field in scenario.initial_state.root and any(
            value != current for value in self.values
        )

    def mutate(self, scenario: Scenario, rng: Random) -> Scenario:
        if not self.applicable(scenario):
            raise ValueError(f"{self.id} is not applicable to Scenario {scenario.id}.")
        current = scenario.initial_state.root[self.field]
        value = deepcopy(rng.choice([value for value in self.values if value != current]))
        state = deepcopy(scenario.initial_state.root)
        state[self.field] = value
        return _finish(
            scenario,
            mutator=self,
            parameters={"field": self.field, "value": value},
            condition=self.condition,
            initial_state=state,
            ground_truth_updates=self.ground_truth_updates,
        )


@dataclass(frozen=True)
class SetToolCondition:
    """Change one declared tool's availability."""

    tools: Sequence[str]
    status: str = "unavailable"
    condition: str = "tool_outage"
    ground_truth_updates: Mapping[str, Any] = dataclass_field(default_factory=dict)
    id: ClassVar[str] = "set_tool_condition"
    version: ClassVar[str] = "1.0"

    def applicable(self, scenario: Scenario) -> bool:
        return any(tool in scenario.tool_conditions for tool in self.tools)

    def mutate(self, scenario: Scenario, rng: Random) -> Scenario:
        candidates = [tool for tool in self.tools if tool in scenario.tool_conditions]
        if not candidates:
            raise ValueError(f"{self.id} is not applicable to Scenario {scenario.id}.")
        tool = rng.choice(candidates)
        conditions = deepcopy(scenario.tool_conditions)
        conditions[tool] = self.status
        return _finish(
            scenario,
            mutator=self,
            parameters={"tool": tool, "status": self.status},
            condition=self.condition,
            tool_conditions=conditions,
            ground_truth_updates=self.ground_truth_updates,
        )


@dataclass(frozen=True)
class ChangePersona:
    """Replace the persona with one configured bounded variant."""

    personas: Sequence[Mapping[str, Any]]
    condition: str = "changed_persona"
    ground_truth_updates: Mapping[str, Any] = dataclass_field(default_factory=dict)
    id: ClassVar[str] = "change_persona"
    version: ClassVar[str] = "1.0"

    def applicable(self, scenario: Scenario) -> bool:
        return any(dict(persona) != scenario.persona for persona in self.personas)

    def mutate(self, scenario: Scenario, rng: Random) -> Scenario:
        if not self.applicable(scenario):
            raise ValueError(f"{self.id} is not applicable to Scenario {scenario.id}.")
        candidates = [persona for persona in self.personas if dict(persona) != scenario.persona]
        persona = deepcopy(dict(rng.choice(candidates)))
        return _finish(
            scenario,
            mutator=self,
            parameters={"persona": persona},
            condition=self.condition,
            persona=persona,
            ground_truth_updates=self.ground_truth_updates,
        )
