"""Reusable execution of one Policy against one Scenario."""

from __future__ import annotations

from collections.abc import Callable

from pearl.policies import Policy, PolicyContext
from pearl.runtime.environment import EnvironmentRuntime
from pearl.spec import Scenario
from pearl.spec.trajectory import (
    PolicyReference,
    Step,
    Trajectory,
    policy_reference,
    trajectory_id_for,
)

Clock = Callable[[], int]


class EpisodeRunner:
    """Execute an Episode and capture a complete immutable Trajectory."""

    def __init__(self, clock_ns: Clock | None = None) -> None:
        self._clock_ns = clock_ns

    async def run(
        self,
        runtime: EnvironmentRuntime,
        policy: Policy,
        scenario: Scenario,
        reference: PolicyReference | None = None,
    ) -> Trajectory:
        fixed_policy = reference or policy_reference(policy.name, policy.version)
        if fixed_policy.name != policy.name or fixed_policy.version != policy.version:
            raise ValueError("PolicyReference name and version must match the executed Policy")
        observation = runtime.reset(scenario)
        steps: list[Step] = []

        while not runtime.is_terminated:
            state_before = runtime.state()
            context = PolicyContext(
                environment_id=runtime.spec.metadata.id,
                environment_version=runtime.spec.metadata.version,
                scenario_id=scenario.id,
                step_index=runtime.step_index,
                metadata={
                    "partition": scenario.partition.value,
                    "scenario_seed": scenario.seed,
                },
            )
            started = self._clock_ns() if self._clock_ns is not None else None
            action = await policy.act(observation.model_copy(deep=True), context)
            result = runtime.step(action)
            latency_ms = 0
            if started is not None and self._clock_ns is not None:
                elapsed_ns = self._clock_ns() - started
                if elapsed_ns < 0:
                    raise ValueError("Episode clock must be monotonic")
                latency_ms = elapsed_ns // 1_000_000

            steps.append(
                Step(
                    index=result.step_index,
                    state_before=state_before.model_dump(mode="json"),
                    observation=observation.model_dump(mode="json"),
                    action=action.model_dump(mode="json"),
                    tool_call=result.tool_call,
                    tool_result=result.tool_result,
                    state_after=result.state.model_dump(mode="json"),
                    latency_ms=latency_ms,
                )
            )
            observation = result.observation

        termination_reason = runtime.termination_reason
        if termination_reason is None:
            raise RuntimeError("EnvironmentRuntime terminated without a reason")

        runtime_metadata = {
            "partition": scenario.partition.value,
            "scenario_seed": scenario.seed,
        }
        trajectory_id = trajectory_id_for(
            environment_id=runtime.spec.metadata.id,
            environment_version=runtime.spec.metadata.version,
            scenario_id=scenario.id,
            policy=fixed_policy,
            steps=steps,
            termination_reason=termination_reason,
            runtime_metadata=runtime_metadata,
        )
        return Trajectory(
            trajectory_id=trajectory_id,
            environment_id=runtime.spec.metadata.id,
            environment_version=runtime.spec.metadata.version,
            scenario_id=scenario.id,
            policy=fixed_policy,
            steps=tuple(steps),
            termination_reason=termination_reason,
            runtime_metadata=runtime_metadata,
        )


async def run_episode(
    runtime: EnvironmentRuntime,
    policy: Policy,
    scenario: Scenario,
    reference: PolicyReference | None = None,
) -> Trajectory:
    """Convenience wrapper around the deterministic default EpisodeRunner."""
    return await EpisodeRunner().run(runtime, policy, scenario, reference)
