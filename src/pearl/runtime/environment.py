"""EnvironmentRuntime protocol and injected deterministic implementation."""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy
from typing import Protocol, runtime_checkable

from pearl.runtime.models import (
    Action,
    Observation,
    RuntimeContext,
    StateTransition,
    StepResult,
)
from pearl.spec import EnvironmentSpec, Scenario, State

ObserveFunction = Callable[[State, RuntimeContext], Observation]
TransitionFunction = Callable[[State, Action, RuntimeContext], StateTransition]


class RuntimeLifecycleError(RuntimeError):
    """An operation was attempted outside the runtime lifecycle."""


class InvalidActionError(ValueError):
    """A Policy selected an undeclared or unavailable action."""


@runtime_checkable
class EnvironmentRuntime(Protocol):
    """Executable behavior corresponding to one declarative EnvironmentSpec."""

    @property
    def spec(self) -> EnvironmentSpec: ...

    def reset(self, scenario: Scenario) -> Observation: ...

    def observe(self) -> Observation: ...

    def step(self, action: Action) -> StepResult: ...

    def state(self) -> State: ...

    @property
    def is_terminated(self) -> bool: ...

    @property
    def termination_reason(self) -> str | None: ...

    @property
    def step_index(self) -> int: ...


class FunctionalEnvironmentRuntime:
    """Deterministic state machine configured with pure environment callbacks."""

    def __init__(
        self,
        spec: EnvironmentSpec,
        observe: ObserveFunction,
        transition: TransitionFunction,
    ) -> None:
        self._spec = spec
        self._observe_function = observe
        self._transition_function = transition
        self._state: State | None = None
        self._scenario: Scenario | None = None
        self._step_index = 0
        self._termination_reason: str | None = None

    @property
    def spec(self) -> EnvironmentSpec:
        return self._spec

    @property
    def is_terminated(self) -> bool:
        return self._termination_reason is not None

    @property
    def termination_reason(self) -> str | None:
        return self._termination_reason

    @property
    def step_index(self) -> int:
        """Number of accepted actions since the last reset."""
        return self._step_index

    def reset(self, scenario: Scenario) -> Observation:
        """Validate a Scenario and restore a fresh state including schema defaults."""
        self._spec.validate_scenario(scenario)
        state = {
            name: deepcopy(field.default)
            for name, field in self._spec.state_schema.items()
            if "default" in field.model_fields_set
        }
        state.update(deepcopy(scenario.initial_state.root))
        next_state = State(state)
        self._validate_runtime_state(next_state)
        next_scenario = scenario.model_copy(deep=True)
        observation = self._observe_function(
            next_state.model_copy(deep=True), self._build_context(next_scenario, 0)
        )
        self._validate_observation(observation, next_state)
        self._state = next_state
        self._scenario = next_scenario
        self._step_index = 0
        self._termination_reason = None
        return observation.model_copy(deep=True)

    def observe(self) -> Observation:
        state = self.state()
        observation = self._observe_function(state, self._context())
        self._validate_observation(observation, state)
        return observation.model_copy(deep=True)

    def state(self) -> State:
        if self._state is None:
            raise RuntimeLifecycleError("EnvironmentRuntime must be reset before use.")
        return self._state.model_copy(deep=True)

    def step(self, action: Action) -> StepResult:
        if self._state is None or self._scenario is None:
            raise RuntimeLifecycleError("EnvironmentRuntime must be reset before use.")
        if self.is_terminated:
            raise RuntimeLifecycleError(
                "EnvironmentRuntime cannot step after termination; reset it first."
            )

        declared_actions = {item.id for item in self._spec.actions}
        if action.id not in declared_actions:
            raise InvalidActionError(
                f'Environment {self._spec.metadata.id} does not declare action "{action.id}".'
            )
        current_observation = self.observe()
        if action.id not in current_observation.available_actions:
            raise InvalidActionError(
                f'Action "{action.id}" is not available from observation '
                f'"{current_observation.id}".'
            )

        transition = self._transition_function(self.state(), action, self._context())
        next_state = transition.state.model_copy(deep=True)
        self._validate_runtime_state(next_state)
        next_step_index = self._step_index + 1

        reason = transition.termination_reason
        if reason is not None:
            declared_reasons = {
                *self._spec.termination.success_conditions,
                *self._spec.termination.failure_conditions,
            }
            if reason not in declared_reasons:
                raise ValueError(
                    f'Environment {self._spec.metadata.id} returned undeclared '
                    f'termination reason "{reason}".'
                )
        elif next_step_index >= self._spec.termination.max_steps:
            reason = "max_steps"

        observation = self._observe_function(
            next_state.model_copy(deep=True),
            self._build_context(self._scenario, next_step_index),
        )
        self._validate_observation(observation, next_state)
        self._state = next_state
        self._step_index = next_step_index
        self._termination_reason = reason
        return StepResult(
            step_index=next_step_index - 1,
            observation=observation.model_copy(deep=True),
            state=self.state(),
            terminated=self.is_terminated,
            termination_reason=reason,
            info=deepcopy(transition.info),
        )

    def _context(self) -> RuntimeContext:
        if self._scenario is None:
            raise RuntimeLifecycleError("EnvironmentRuntime must be reset before use.")
        return self._build_context(self._scenario, self._step_index)

    def _build_context(self, scenario: Scenario, step_index: int) -> RuntimeContext:
        return RuntimeContext(
            environment_id=self._spec.metadata.id,
            environment_version=self._spec.metadata.version,
            scenario_id=scenario.id,
            scenario_seed=scenario.seed,
            step_index=step_index,
            persona=deepcopy(scenario.persona),
            conditions=scenario.conditions,
            tool_conditions=deepcopy(scenario.tool_conditions),
        )

    def _validate_runtime_state(self, state: State) -> None:
        unknown = set(state.root) - set(self._spec.state_schema)
        if unknown:
            names = ", ".join(sorted(unknown))
            raise ValueError(
                f"Environment {self._spec.metadata.id} runtime produced unknown state "
                f"fields: {names}."
            )
        missing = {
            name
            for name, field in self._spec.state_schema.items()
            if field.required and name not in state.root
        }
        if missing:
            names = ", ".join(sorted(missing))
            raise ValueError(
                f"Environment {self._spec.metadata.id} runtime omitted required state "
                f"fields: {names}."
            )
        for name, value in state.root.items():
            self._spec.validate_state_value(name, value, owner="runtime")

    def _validate_observation(self, observation: Observation, state: State) -> None:
        observation_specs = {item.id: item for item in self._spec.observations}
        if observation.id not in observation_specs:
            raise ValueError(
                f'Environment {self._spec.metadata.id} runtime produced undeclared '
                f'observation "{observation.id}".'
            )
        expected_fields = set(observation_specs[observation.id].state_fields) & set(
            state.root
        )
        actual_fields = set(observation.data)
        if actual_fields != expected_fields:
            missing = ", ".join(sorted(expected_fields - actual_fields)) or "none"
            extra = ", ".join(sorted(actual_fields - expected_fields)) or "none"
            raise ValueError(
                f'Observation "{observation.id}" does not match its state projection; '
                f"missing: {missing}; extra: {extra}."
            )
        mismatched = {
            name
            for name, value in observation.data.items()
            if value != state.root[name]
        }
        if mismatched:
            names = ", ".join(sorted(mismatched))
            raise ValueError(
                f'Observation "{observation.id}" does not faithfully project state '
                f"fields: {names}."
            )
        declared_actions = {item.id for item in self._spec.actions}
        unknown_actions = set(observation.available_actions) - declared_actions
        if unknown_actions:
            names = ", ".join(sorted(unknown_actions))
            raise ValueError(
                f'Observation "{observation.id}" exposes undeclared actions: {names}.'
            )
        if len(set(observation.available_actions)) != len(observation.available_actions):
            raise ValueError(
                f'Observation "{observation.id}" exposes duplicate available actions.'
            )
