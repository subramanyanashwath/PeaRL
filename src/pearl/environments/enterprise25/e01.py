"""Deterministic Day 4 runtime for E01 Claims Dispute Resolution."""

from __future__ import annotations

from collections.abc import Callable
from copy import deepcopy

from pearl.policies import PolicyContext, Rule, RulePolicy
from pearl.runtime import (
    Action,
    FunctionalEnvironmentRuntime,
    InvalidActionError,
    Observation,
    RuntimeContext,
    StateTransition,
)
from pearl.scenarios.distribution import resolve_environment_path
from pearl.spec import State, load_environment_spec


def create_e01_runtime() -> FunctionalEnvironmentRuntime:
    """Load E01's declaration and bind its deterministic state transitions."""
    spec = load_environment_spec(resolve_environment_path("E01") / "environment.yaml")
    return FunctionalEnvironmentRuntime(spec, _observe, _transition)


def create_e01_baseline_policy() -> RulePolicy:
    """Return the deterministic baseline required by the Day 5 Run gate."""
    return RulePolicy(
        name="baseline",
        version="1.0",
        rules=(
            Rule(_in_phase("intake"), Action(id="inspect_evidence")),
            Rule(_in_phase("policy_review"), Action(id="retrieve_policy")),
            Rule(_in_phase("decision"), _baseline_decision),
        ),
    )


def _in_phase(phase: str) -> Callable[[Observation, PolicyContext], bool]:
    def predicate(observation: Observation, context: PolicyContext) -> bool:
        return str(observation.data["review_phase"]) == phase

    return predicate


def _baseline_decision(observation: Observation, context: PolicyContext) -> Action:
    if (
        observation.data["claims_retrieval_status"] != "retrieved"
        or observation.data["policy_retrieval_status"] != "retrieved"
        or observation.data["policy_conflict"] is True
    ):
        return Action(id="escalate_claim")
    if (
        observation.data["documentation_complete"] is False
        or "evidence_summary" not in observation.data
    ):
        resolution = "request_more_evidence"
    elif "excluded" in str(observation.data["evidence_summary"]).lower():
        resolution = "uphold_denial"
    else:
        resolution = "approve"
    return Action(id="resolve_claim", arguments={"resolution": resolution})


def _observe(state: State, context: RuntimeContext) -> Observation:
    phase = str(state.root["review_phase"])
    observation_id, actions = {
        "intake": ("claim_intake", ("inspect_evidence",)),
        "policy_review": ("policy_review", ("retrieve_policy",)),
        "decision": ("decision_context", ("resolve_claim", "escalate_claim")),
        "complete": ("resolution", ()),
    }[phase]
    visible_fields = {
        "claim_intake": (
            "review_phase",
            "claim_status",
            "documentation_complete",
            "evidence_summary",
            "policy_conflict",
            "claim_amount",
        ),
        "policy_review": (
            "review_phase",
            "claim_status",
            "documentation_complete",
            "evidence_summary",
            "policy_conflict",
            "claim_amount",
            "claims_retrieval_status",
        ),
        "decision_context": (
            "review_phase",
            "claim_status",
            "documentation_complete",
            "evidence_summary",
            "policy_conflict",
            "claim_amount",
            "claims_retrieval_status",
            "policy_retrieval_status",
            "policy_summary",
        ),
        "resolution": ("review_phase", "claim_status", "resolution"),
    }[observation_id]
    data = {
        name: deepcopy(state.root[name]) for name in visible_fields if name in state.root
    }
    return Observation(id=observation_id, data=data, available_actions=actions)


def _transition(
    state: State, action: Action, context: RuntimeContext
) -> StateTransition:
    phase = state.root["review_phase"]
    next_state = deepcopy(state.root)

    if phase == "intake" and action.id == "inspect_evidence":
        _require_arguments(action, set())
        if context.tool_conditions.get("claims_api") == "healthy":
            next_state["claims_retrieval_status"] = "retrieved"
        else:
            next_state["claims_retrieval_status"] = "unavailable"
        next_state["review_phase"] = "policy_review"
        return StateTransition(
            state=State(next_state),
            tool_call={"tool_id": "claims_api", "arguments": {}},
            tool_result={"status": next_state["claims_retrieval_status"]},
        )

    if phase == "policy_review" and action.id == "retrieve_policy":
        _require_arguments(action, set())
        if context.tool_conditions.get("policy_store") == "healthy":
            next_state["policy_retrieval_status"] = "retrieved"
            next_state["policy_summary"] = "Controlling policy record retrieved."
        else:
            next_state["policy_retrieval_status"] = "unavailable"
            next_state.pop("policy_summary", None)
        next_state["review_phase"] = "decision"
        return StateTransition(
            state=State(next_state),
            tool_call={"tool_id": "policy_store", "arguments": {}},
            tool_result={"status": next_state["policy_retrieval_status"]},
        )

    if phase == "decision" and action.id == "resolve_claim":
        _require_arguments(action, {"resolution"})
        resolution = action.arguments["resolution"]
        permitted = {"approve", "request_more_evidence", "uphold_denial"}
        if not isinstance(resolution, str) or resolution not in permitted:
            raise InvalidActionError(
                "resolve_claim requires resolution to be approve, "
                "request_more_evidence, or uphold_denial."
            )
        next_state.update(
            review_phase="complete", claim_status="resolved", resolution=resolution
        )
        return StateTransition(
            state=State(next_state),
            termination_reason="resolved",
            info={"resolution": resolution},
        )

    if phase == "decision" and action.id == "escalate_claim":
        _require_arguments(action, set())
        next_state.update(
            review_phase="complete", claim_status="escalated", resolution="escalate"
        )
        return StateTransition(
            state=State(next_state),
            termination_reason="escalated",
            info={"resolution": "escalate"},
        )

    raise InvalidActionError(f'Action "{action.id}" is invalid during E01 phase "{phase}".')


def _require_arguments(action: Action, expected: set[str]) -> None:
    actual = set(action.arguments)
    if actual != expected:
        missing = ", ".join(sorted(expected - actual)) or "none"
        extra = ", ".join(sorted(actual - expected)) or "none"
        raise InvalidActionError(
            f'Action "{action.id}" arguments do not match its contract; '
            f"missing: {missing}; extra: {extra}."
        )
