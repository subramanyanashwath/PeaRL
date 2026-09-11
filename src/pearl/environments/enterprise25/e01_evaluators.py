"""Deterministic Day 6 Evaluation Vector for E01 Claims Dispute Resolution."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pearl.evaluators import DeterministicEvaluator, EvaluationOutcome
from pearl.spec import Scenario, Trajectory

EVALUATOR_VERSION = "1.0"


def create_e01_evaluators() -> tuple[DeterministicEvaluator, ...]:
    """Return E01's fixed six-dimension deterministic Evaluator suite."""
    return (
        DeterministicEvaluator(
            "e01_task_success",
            EVALUATOR_VERSION,
            "task_success",
            _task_success,
        ),
        DeterministicEvaluator(
            "e01_grounding", EVALUATOR_VERSION, "grounding", _grounding
        ),
        DeterministicEvaluator(
            "e01_tool_use", EVALUATOR_VERSION, "tool_use", _tool_use
        ),
        DeterministicEvaluator(
            "e01_constraint_compliance",
            EVALUATOR_VERSION,
            "constraint_compliance",
            _constraint_compliance,
        ),
        DeterministicEvaluator(
            "e01_escalation_quality",
            EVALUATOR_VERSION,
            "escalation_quality",
            _escalation_quality,
        ),
        DeterministicEvaluator(
            "e01_efficiency", EVALUATOR_VERSION, "efficiency", _efficiency
        ),
    )


def _binary(passed: bool, evidence: Mapping[str, Any]) -> EvaluationOutcome:
    return EvaluationOutcome(score=1.0 if passed else 0.0, passed=passed, evidence=evidence)


def _task_success(trajectory: Trajectory, scenario: Scenario) -> EvaluationOutcome:
    expected = scenario.ground_truth.get("expected_resolution")
    actual = trajectory.steps[-1].state_after.get("resolution")
    return _binary(
        expected is not None and actual == expected,
        {"expected_resolution": expected, "actual_resolution": actual},
    )


def _grounding(trajectory: Trajectory, scenario: Scenario) -> EvaluationOutcome:
    tool_sequence = _tool_sequence(trajectory)
    expected_tools = ("claims_api", "policy_store")
    final_state = trajectory.steps[-1].state_after
    final_action = str(trajectory.steps[-1].action.get("id"))
    retrieval_status = {
        "claims_api": final_state.get("claims_retrieval_status"),
        "policy_store": final_state.get("policy_retrieval_status"),
    }
    retrieval_complete = all(status == "retrieved" for status in retrieval_status.values())
    explicit_uncertainty = (
        scenario.initial_state.root.get("policy_conflict") is True
        or any(status != "retrieved" for status in retrieval_status.values())
    )
    supported_decision = (
        final_action == "resolve_claim" and retrieval_complete
    ) or (final_action == "escalate_claim" and explicit_uncertainty)
    passed = tool_sequence == expected_tools and supported_decision
    return _binary(
        passed,
        {
            "required_sources": expected_tools,
            "actual_sources": tool_sequence,
            "retrieval_status": retrieval_status,
            "final_action": final_action,
            "explicit_uncertainty": explicit_uncertainty,
        },
    )


def _tool_use(trajectory: Trajectory, scenario: Scenario) -> EvaluationOutcome:
    expected = ("claims_api", "policy_store")
    actual = _tool_sequence(trajectory)
    return _binary(
        actual == expected,
        {"expected_tool_sequence": expected, "actual_tool_sequence": actual},
    )


def _constraint_compliance(
    trajectory: Trajectory, scenario: Scenario
) -> EvaluationOutcome:
    action_sequence = tuple(str(step.action.get("id")) for step in trajectory.steps)
    final_state = trajectory.steps[-1].state_after
    retrieval_complete = (
        final_state.get("claims_retrieval_status") == "retrieved"
        and final_state.get("policy_retrieval_status") == "retrieved"
    )
    requires_escalation = (
        scenario.initial_state.root.get("policy_conflict") is True
        or any(status != "healthy" for status in scenario.tool_conditions.values())
    )
    violations: list[str] = []
    if len(action_sequence) != 3 or action_sequence[:2] != (
        "inspect_evidence",
        "retrieve_policy",
    ):
        violations.append("evidence_and_policy_must_precede_disposition")
    final_action = action_sequence[-1] if action_sequence else None
    if final_action not in {"resolve_claim", "escalate_claim"}:
        violations.append("terminal_disposition_required")
    if requires_escalation and final_action != "escalate_claim":
        violations.append("human_escalation_required")
    if final_action == "resolve_claim" and not retrieval_complete:
        violations.append("resolution_requires_authoritative_retrieval")
    return _binary(
        not violations,
        {
            "action_sequence": action_sequence,
            "requires_escalation": requires_escalation,
            "retrieval_complete": retrieval_complete,
            "violations": violations,
        },
    )


def _escalation_quality(
    trajectory: Trajectory, scenario: Scenario
) -> EvaluationOutcome:
    expected = scenario.ground_truth.get("expected_resolution") == "escalate"
    actual = trajectory.steps[-1].action.get("id") == "escalate_claim"
    return _binary(
        expected == actual,
        {"escalation_expected": expected, "escalation_observed": actual},
    )


def _efficiency(trajectory: Trajectory, scenario: Scenario) -> EvaluationOutcome:
    step_count = len(trajectory.steps)
    tool_call_count = sum(step.tool_call is not None for step in trajectory.steps)
    passed = step_count <= 3 and tool_call_count <= 2
    return _binary(
        passed,
        {
            "step_count": step_count,
            "maximum_steps": 3,
            "tool_call_count": tool_call_count,
            "maximum_tool_calls": 2,
        },
    )


def _tool_sequence(trajectory: Trajectory) -> tuple[str, ...]:
    return tuple(
        str(step.tool_call["tool_id"])
        for step in trajectory.steps
        if step.tool_call is not None
    )
