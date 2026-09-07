from __future__ import annotations

import asyncio
import json

import pytest
from pydantic import ValidationError

from pearl.policies import (
    CallablePolicy,
    LegacyGnomonAgentPolicy,
    Policy,
    PolicyContext,
    PolicyError,
    Rule,
    RulePolicy,
)
from pearl.runtime import Action, Observation


def observation() -> Observation:
    return Observation(
        id="decision_context",
        data={"review_phase": "decision"},
        available_actions=("resolve_claim",),
    )


def context() -> PolicyContext:
    return PolicyContext(
        environment_id="enterprise25.E01",
        environment_version=1,
        scenario_id="E01.S001",
        step_index=2,
    )


def test_rule_policy_uses_first_matching_rule() -> None:
    policy = RulePolicy(
        name="rules",
        version="1.0",
        rules=(
            Rule(lambda obs, ctx: True, Action(id="resolve_claim", arguments={"n": 1})),
            Rule(lambda obs, ctx: True, Action(id="ignored")),
        ),
    )

    action = asyncio.run(policy.act(observation(), context()))

    assert action == Action(id="resolve_claim", arguments={"n": 1})
    assert isinstance(policy, Policy)


def test_rule_policy_supports_action_factories() -> None:
    policy = RulePolicy(
        name="factory",
        version="1.0",
        rules=(Rule(lambda obs, ctx: True, lambda obs, ctx: Action(id=obs.id)),),
    )

    assert asyncio.run(policy.act(observation(), context())).id == "decision_context"


def test_rule_policy_fails_when_no_rule_matches() -> None:
    policy = RulePolicy(
        name="empty",
        version="1.0",
        rules=(Rule(lambda obs, ctx: False, Action(id="never")),),
    )

    with pytest.raises(PolicyError, match="no matching rule"):
        asyncio.run(policy.act(observation(), context()))


def test_callable_policy_adapts_sync_function() -> None:
    policy = CallablePolicy(
        name="sync",
        version="1.0",
        function=lambda obs, ctx: Action(id=obs.available_actions[0]),
    )

    assert asyncio.run(policy.act(observation(), context())).id == "resolve_claim"
    assert isinstance(policy, Policy)


def test_callable_policy_adapts_async_function() -> None:
    async def select(obs: Observation, ctx: PolicyContext) -> Action:
        return Action(id=f"step_{ctx.step_index}")

    policy = CallablePolicy(name="async", version="1.0", function=select)

    assert asyncio.run(policy.act(observation(), context())).id == "step_2"


def test_policy_context_forbids_ground_truth() -> None:
    with pytest.raises(ValidationError, match="ground_truth"):
        PolicyContext.model_validate(
            {
                **context().model_dump(),
                "ground_truth": {"expected_resolution": "approve"},
            }
        )


class RecordingLegacyAgent:
    name = "gnomon-agent"

    def __init__(self) -> None:
        self.input: str | None = None

    def run(self, input: str) -> str:
        self.input = input
        return "resolve_claim"


def test_legacy_gnomon_adapter_preserves_contract_without_dependency() -> None:
    agent = RecordingLegacyAgent()
    policy = LegacyGnomonAgentPolicy(
        agent=agent,
        output_parser=lambda output: Action(id=output),
    )

    action = asyncio.run(policy.act(observation(), context()))

    assert action.id == "resolve_claim"
    assert policy.name == "gnomon-agent"
    assert policy.version == "legacy"
    assert isinstance(policy, Policy)
    assert agent.input is not None
    payload = json.loads(agent.input)
    assert payload["observation"]["id"] == "decision_context"
    assert payload["context"]["scenario_id"] == "E01.S001"
