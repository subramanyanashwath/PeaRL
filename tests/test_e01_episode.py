from __future__ import annotations

import asyncio

from pearl.environments.enterprise25 import create_e01_runtime
from pearl.policies import PolicyContext, Rule, RulePolicy
from pearl.runtime import Action, EnvironmentRuntime, Observation, StepResult
from pearl.scenarios import load_scenario_distribution
from pearl.spec import Scenario


def _phase(name: str):
    return lambda observation, context: observation.data["review_phase"] == name


def _decision(observation: Observation, context: PolicyContext) -> Action:
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


def policy() -> RulePolicy:
    return RulePolicy(
        name="e01_day4_rules",
        version="1.0",
        rules=(
            Rule(_phase("intake"), Action(id="inspect_evidence")),
            Rule(_phase("policy_review"), Action(id="retrieve_policy")),
            Rule(_phase("decision"), _decision),
        ),
    )


async def _execute(
    runtime: EnvironmentRuntime, scenario: Scenario
) -> tuple[StepResult, ...]:
    observation = runtime.reset(scenario)
    results: list[StepResult] = []
    while not runtime.is_terminated:
        context = PolicyContext(
            environment_id=runtime.spec.metadata.id,
            environment_version=runtime.spec.metadata.version,
            scenario_id=scenario.id,
            step_index=len(results),
            metadata={"partition": scenario.partition.value},
        )
        action = await policy().act(observation, context)
        result = runtime.step(action)
        results.append(result)
        observation = result.observation
    return tuple(results)


def test_complete_multistep_e01_episode_executes() -> None:
    scenario = load_scenario_distribution("E01").sample(1, 42)[0]

    results = asyncio.run(_execute(create_e01_runtime(), scenario))

    assert len(results) == 3
    assert [result.step_index for result in results] == [0, 1, 2]
    assert results[-1].terminated is True
    assert results[-1].termination_reason in {"resolved", "escalated"}
    assert results[-1].observation.id == "resolution"


def test_e01_episode_is_deterministic_for_same_scenario_and_policy() -> None:
    scenario = load_scenario_distribution("E01").sample(1, 42)[0]

    first = asyncio.run(_execute(create_e01_runtime(), scenario))
    second = asyncio.run(_execute(create_e01_runtime(), scenario))

    assert first == second


def test_all_day3_exit_gate_scenarios_execute_to_termination() -> None:
    scenarios = load_scenario_distribution("E01").sample(50, 42)

    results = [
        asyncio.run(_execute(create_e01_runtime(), scenario)) for scenario in scenarios
    ]

    assert all(len(episode) == 3 for episode in results)
    assert all(episode[-1].terminated for episode in results)
