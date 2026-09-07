from __future__ import annotations

from copy import deepcopy

import pytest

from pearl.environments.enterprise25 import create_e01_runtime
from pearl.runtime import (
    Action,
    EnvironmentRuntime,
    FunctionalEnvironmentRuntime,
    InvalidActionError,
    Observation,
    RuntimeContext,
    RuntimeLifecycleError,
    StateTransition,
)
from pearl.spec import Scenario, State
from pearl.spec.scenario import ScenarioProvenance


def scenario(*, policy_store: str = "healthy") -> Scenario:
    return Scenario(
        id="E01.runtime.001",
        environment_id="enterprise25.E01",
        seed=1,
        initial_state={
            "claim_status": "denied",
            "documentation_complete": True,
            "evidence_summary": "Covered loss with complete evidence.",
            "policy_conflict": False,
            "claim_amount": 4800,
        },
        tool_conditions={"policy_store": policy_store, "claims_api": "healthy"},
        ground_truth={"expected_resolution": "approve"},
    )


def test_e01_runtime_satisfies_protocol() -> None:
    assert isinstance(create_e01_runtime(), EnvironmentRuntime)


def test_runtime_requires_reset_before_observe_state_or_step() -> None:
    runtime = create_e01_runtime()

    with pytest.raises(RuntimeLifecycleError, match="reset before use"):
        runtime.observe()
    with pytest.raises(RuntimeLifecycleError, match="reset before use"):
        runtime.state()
    with pytest.raises(RuntimeLifecycleError, match="reset before use"):
        runtime.step(Action(id="inspect_evidence"))


def test_reset_fills_spec_defaults_and_returns_declared_projection() -> None:
    runtime = create_e01_runtime()

    observation = runtime.reset(scenario())

    assert runtime.state().root["review_phase"] == "intake"
    assert runtime.step_index == 0
    assert runtime.state().root["policy_retrieval_status"] == "not_attempted"
    assert observation.id == "claim_intake"
    assert observation.available_actions == ("inspect_evidence",)
    assert "expected_resolution" not in observation.data


def test_runtime_rejects_scenario_from_another_environment_version() -> None:
    wrong_version = scenario().model_copy(
        update={"provenance": ScenarioProvenance(environment_version=2)}
    )

    with pytest.raises(ValueError, match="generated for environment version 2"):
        create_e01_runtime().reset(wrong_version)


def test_runtime_state_snapshots_do_not_mutate_internal_state() -> None:
    runtime = create_e01_runtime()
    runtime.reset(scenario())
    snapshot = runtime.state()

    snapshot.root["review_phase"] = "tampered"

    assert runtime.state().root["review_phase"] == "intake"


def test_runtime_rejects_undeclared_and_currently_unavailable_actions() -> None:
    runtime = create_e01_runtime()
    runtime.reset(scenario())

    with pytest.raises(InvalidActionError, match="does not declare"):
        runtime.step(Action(id="invented_action"))
    with pytest.raises(InvalidActionError, match="not available"):
        runtime.step(Action(id="resolve_claim", arguments={"resolution": "approve"}))


def test_e01_healthy_path_is_three_steps_and_terminates() -> None:
    runtime = create_e01_runtime()
    runtime.reset(scenario())

    inspected = runtime.step(Action(id="inspect_evidence"))
    retrieved = runtime.step(Action(id="retrieve_policy"))
    resolved = runtime.step(
        Action(id="resolve_claim", arguments={"resolution": "approve"})
    )

    assert inspected.step_index == 0
    assert inspected.observation.id == "policy_review"
    assert retrieved.step_index == 1
    assert retrieved.observation.data["policy_retrieval_status"] == "retrieved"
    assert resolved.step_index == 2
    assert runtime.step_index == 3
    assert resolved.terminated is True
    assert resolved.termination_reason == "resolved"
    assert resolved.observation.id == "resolution"
    assert resolved.state.root["resolution"] == "approve"
    with pytest.raises(RuntimeLifecycleError, match="after termination"):
        runtime.step(Action(id="escalate_claim"))


def test_e01_tool_outage_is_observable_before_escalation() -> None:
    runtime = create_e01_runtime()
    runtime.reset(scenario(policy_store="unavailable"))

    runtime.step(Action(id="inspect_evidence"))
    retrieval = runtime.step(Action(id="retrieve_policy"))
    escalation = runtime.step(Action(id="escalate_claim"))

    assert retrieval.observation.data["policy_retrieval_status"] == "unavailable"
    assert escalation.termination_reason == "escalated"


def test_e01_claims_api_outage_is_observable() -> None:
    broken = scenario().model_copy(
        update={"tool_conditions": {"policy_store": "healthy", "claims_api": "unavailable"}}
    )
    runtime = create_e01_runtime()
    runtime.reset(broken)

    inspection = runtime.step(Action(id="inspect_evidence"))

    assert inspection.observation.data["claims_retrieval_status"] == "unavailable"


def test_e01_action_argument_contract_is_enforced() -> None:
    runtime = create_e01_runtime()
    runtime.reset(scenario())
    runtime.step(Action(id="inspect_evidence"))
    runtime.step(Action(id="retrieve_policy"))

    with pytest.raises(InvalidActionError, match="arguments do not match"):
        runtime.step(Action(id="resolve_claim"))
    with pytest.raises(InvalidActionError, match="requires resolution"):
        runtime.step(Action(id="resolve_claim", arguments={"resolution": "invented"}))


def test_runtime_enforces_max_steps() -> None:
    source = create_e01_runtime().spec
    spec = source.model_copy(
        update={"termination": source.termination.model_copy(update={"max_steps": 1})}
    )

    def observe(state: State, context: RuntimeContext) -> Observation:
        names = spec.observations[0].state_fields
        return Observation(
            id="claim_intake",
            data={name: state.root[name] for name in names if name in state.root},
            available_actions=("inspect_evidence",),
        )

    def transition(
        state: State, action: Action, context: RuntimeContext
    ) -> StateTransition:
        return StateTransition(state=state)

    runtime = FunctionalEnvironmentRuntime(spec, observe, transition)
    runtime.reset(scenario())

    result = runtime.step(Action(id="inspect_evidence"))

    assert result.terminated is True
    assert result.termination_reason == "max_steps"


def test_runtime_rejects_invalid_transition_state() -> None:
    source = create_e01_runtime()

    def observe(state: State, context: RuntimeContext) -> Observation:
        names = source.spec.observations[0].state_fields
        return Observation(
            id="claim_intake",
            data={name: state.root[name] for name in names if name in state.root},
            available_actions=("inspect_evidence",),
        )

    def transition(
        state: State, action: Action, context: RuntimeContext
    ) -> StateTransition:
        broken = deepcopy(state.root)
        broken["undeclared"] = True
        return StateTransition(state=State(broken))

    runtime = FunctionalEnvironmentRuntime(source.spec, observe, transition)
    runtime.reset(scenario())

    with pytest.raises(ValueError, match="unknown state fields"):
        runtime.step(Action(id="inspect_evidence"))


def test_runtime_rejects_observation_that_lies_about_state() -> None:
    source = create_e01_runtime()

    def observe(state: State, context: RuntimeContext) -> Observation:
        names = source.spec.observations[0].state_fields
        data = {name: state.root[name] for name in names if name in state.root}
        data["claim_status"] = "fabricated"
        return Observation(
            id="claim_intake",
            data=data,
            available_actions=("inspect_evidence",),
        )

    runtime = FunctionalEnvironmentRuntime(
        source.spec,
        observe,
        lambda state, action, context: StateTransition(state=state),
    )

    with pytest.raises(ValueError, match="faithfully project"):
        runtime.reset(scenario())
    with pytest.raises(RuntimeLifecycleError, match="reset before use"):
        runtime.state()
