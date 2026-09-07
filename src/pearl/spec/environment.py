"""Declarative environment specification and cross-reference validation."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from pearl.spec.scenario import Scenario

StateValueType = Literal["string", "integer", "number", "boolean", "object", "array"]
MetricType = Literal["binary", "continuous", "ordinal", "categorical"]
GateOperator = Literal["gte", "lte", "max_regression"]


class FrozenModel(BaseModel):
    """Strict, immutable base for serializable specifications."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class EnvironmentMetadata(FrozenModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    version: int = Field(ge=1)
    vertical: str = Field(min_length=1, pattern=r"^[a-z][a-z0-9_]*$")
    workflow_archetype: str = Field(min_length=1, pattern=r"^[a-z][a-z0-9_]*$")
    tags: tuple[str, ...] = ()


class Objective(FrozenModel):
    task: str = Field(min_length=1, pattern=r"^[a-z][a-z0-9_]*$")
    business_goal: str = Field(min_length=1)


class Actor(FrozenModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    role: str = Field(min_length=1)
    description: str | None = None


class StateField(FrozenModel):
    type: StateValueType
    description: str = Field(min_length=1)
    required: bool = True
    default: Any = None

    @model_validator(mode="after")
    def validate_default(self) -> StateField:
        if "default" not in self.model_fields_set:
            return self
        if not _matches_state_type(self.default, self.type):
            raise ValueError(
                f"default {self.default!r} does not match declared state type {self.type!r}"
            )
        return self


class Observation(FrozenModel):
    id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    state_fields: tuple[str, ...] = ()


class ToolSpec(FrozenModel):
    id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)


class Action(FrozenModel):
    id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    tool_id: str | None = None
    observation_id: str | None = None
    input_schema: dict[str, Any] = Field(default_factory=dict)


class Constraint(FrozenModel):
    id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    action_ids: tuple[str, ...] = ()


class GroundTruth(FrozenModel):
    id: str = Field(min_length=1)
    description: str = Field(min_length=1)
    state_values: dict[str, Any] = Field(default_factory=dict)


class TerminationSpec(FrozenModel):
    max_steps: int = Field(gt=0)
    success_conditions: tuple[str, ...]
    failure_conditions: tuple[str, ...]


class EvaluationDimension(FrozenModel):
    id: str = Field(min_length=1, pattern=r"^[a-z][a-z0-9_]*$")
    description: str = Field(min_length=1)
    metric_type: MetricType


class EvaluatorSpec(FrozenModel):
    id: str = Field(min_length=1)
    dimension: str = Field(min_length=1)


class HardGate(FrozenModel):
    metric: str = Field(min_length=1)
    operator: GateOperator
    value: float


class EvaluationSpec(FrozenModel):
    dimensions: tuple[EvaluationDimension, ...]
    evaluators: tuple[EvaluatorSpec, ...] = ()
    hard_gates: tuple[HardGate, ...]


class ProvenanceEntry(FrozenModel):
    source: str | None = None
    source_id: str | None = None
    notes: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ACTRWProvenance(FrozenModel):
    agency: ProvenanceEntry
    context: ProvenanceEntry
    truth: ProvenanceEntry
    risk: ProvenanceEntry
    workflow: ProvenanceEntry


class Provenance(FrozenModel):
    objective: ProvenanceEntry
    actrw: ACTRWProvenance


class EnvironmentSpec(FrozenModel):
    """Serializable definition of an environment; never an executable runtime."""

    pearl_spec_version: Literal["1.0"]
    metadata: EnvironmentMetadata
    objective: Objective
    actors: tuple[Actor, ...]
    state_schema: dict[str, StateField]
    observations: tuple[Observation, ...]
    actions: tuple[Action, ...]
    tools: tuple[ToolSpec, ...]
    constraints: tuple[Constraint, ...]
    ground_truth: tuple[GroundTruth, ...]
    termination: TerminationSpec
    evaluation: EvaluationSpec
    provenance: Provenance

    @model_validator(mode="after")
    def validate_references(self) -> EnvironmentSpec:
        environment_id = self.metadata.id
        state_fields = set(self.state_schema)
        observation_ids = _unique_ids(environment_id, "observation", self.observations)
        action_ids = _unique_ids(environment_id, "action", self.actions)
        tool_ids = _unique_ids(environment_id, "tool", self.tools)
        _unique_ids(environment_id, "actor", self.actors)
        _unique_ids(environment_id, "constraint", self.constraints)
        _unique_ids(environment_id, "ground-truth entry", self.ground_truth)

        dimensions = _unique_ids(
            environment_id, "evaluation dimension", self.evaluation.dimensions
        )
        _unique_ids(environment_id, "evaluator", self.evaluation.evaluators)

        for observation in self.observations:
            for field_name in observation.state_fields:
                if field_name not in state_fields:
                    raise ValueError(
                        f'Environment {environment_id} observation "{observation.id}" '
                        f'references state field "{field_name}", but it is not defined '
                        "in state_schema."
                    )

        for action in self.actions:
            if action.tool_id is not None and action.tool_id not in tool_ids:
                raise ValueError(
                    f'Environment {environment_id} references tool "{action.tool_id}" '
                    f'in action "{action.id}", but no tool with id '
                    f'"{action.tool_id}" is defined.'
                )
            if action.observation_id is not None and action.observation_id not in observation_ids:
                raise ValueError(
                    f'Environment {environment_id} action "{action.id}" references '
                    f'observation "{action.observation_id}", but it is not defined.'
                )

        for constraint in self.constraints:
            for action_id in constraint.action_ids:
                if action_id not in action_ids:
                    raise ValueError(
                        f'Environment {environment_id} constraint "{constraint.id}" '
                        f'references action "{action_id}", but it is not defined.'
                    )

        for truth in self.ground_truth:
            for field_name, value in truth.state_values.items():
                if field_name not in state_fields:
                    raise ValueError(
                        f'Environment {environment_id} ground-truth entry "{truth.id}" '
                        f'references state field "{field_name}", but it is not defined.'
                    )
                field_spec = self.state_schema[field_name]
                if not _matches_state_type(value, field_spec.type):
                    raise ValueError(
                        f'Environment {environment_id} ground-truth entry "{truth.id}" '
                        f'gives state field "{field_name}" value {value!r}, which does '
                        f'not match declared type "{field_spec.type}".'
                    )

        for evaluator in self.evaluation.evaluators:
            if evaluator.dimension not in dimensions:
                raise ValueError(
                    f'Environment {environment_id} evaluator "{evaluator.id}" references '
                    f'dimension "{evaluator.dimension}", but it is not defined.'
                )

        for gate in self.evaluation.hard_gates:
            if gate.metric not in dimensions:
                raise ValueError(
                    f'Environment {environment_id} Hard Gate references metric '
                    f'"{gate.metric}", but no evaluation dimension with that id is defined.'
                )

        return self

    def validate_scenario(self, scenario: Scenario) -> None:
        """Validate references from one Scenario into this specification."""
        environment_id = self.metadata.id
        if scenario.environment_id != environment_id:
            raise ValueError(
                f'Scenario {scenario.id} references environment "{scenario.environment_id}", '
                f'but was loaded for environment "{environment_id}".'
            )
        scenario_version = scenario.provenance.environment_version
        if scenario_version is not None and scenario_version != self.metadata.version:
            raise ValueError(
                f"Scenario {scenario.id} was generated for environment version "
                f"{scenario_version}, but {environment_id} is version "
                f"{self.metadata.version}."
            )

        unknown_state = set(scenario.initial_state.root) - set(self.state_schema)
        if unknown_state:
            names = ", ".join(sorted(unknown_state))
            raise ValueError(
                f"Scenario {scenario.id} defines unknown initial-state fields for "
                f"environment {environment_id}: {names}."
            )

        missing_required = {
            name
            for name, field_spec in self.state_schema.items()
            if field_spec.required
            and "default" not in field_spec.model_fields_set
            and name not in scenario.initial_state.root
        }
        if missing_required:
            names = ", ".join(sorted(missing_required))
            raise ValueError(
                f"Scenario {scenario.id} is missing required initial-state fields for "
                f"environment {environment_id}: {names}."
            )

        for name, value in scenario.initial_state.root.items():
            self.validate_state_value(name, value, owner=f"Scenario {scenario.id}")

        tool_ids = {tool.id for tool in self.tools}
        unknown_tools = set(scenario.tool_conditions) - tool_ids
        if unknown_tools:
            names = ", ".join(sorted(unknown_tools))
            raise ValueError(
                f"Scenario {scenario.id} defines conditions for unknown tools in "
                f"environment {environment_id}: {names}."
            )

    def validate_state_value(self, name: str, value: Any, *, owner: str) -> None:
        """Validate one state value against this declarative schema."""
        if name not in self.state_schema:
            raise ValueError(
                f'{owner} gives unknown state field "{name}" for '
                f"environment {self.metadata.id}."
            )
        field_spec = self.state_schema[name]
        if not _matches_state_type(value, field_spec.type):
            raise ValueError(
                f'{owner} gives state field "{name}" value {value!r}, which does '
                f'not match declared type "{field_spec.type}".'
            )


def _unique_ids(environment_id: str, kind: str, values: Iterable[Any]) -> set[str]:
    seen: set[str] = set()
    for value in values:
        if value.id in seen:
            raise ValueError(
                f'Environment {environment_id} contains duplicate {kind} id "{value.id}".'
            )
        seen.add(value.id)
    return seen


def _matches_state_type(value: Any, declared: StateValueType) -> bool:
    if declared == "string":
        return isinstance(value, str)
    if declared == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if declared == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if declared == "boolean":
        return isinstance(value, bool)
    if declared == "object":
        return isinstance(value, dict)
    return isinstance(value, list)
