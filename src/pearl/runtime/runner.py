"""Ordered batch execution and reproducible Run assembly."""

from __future__ import annotations

import hashlib
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from pearl.policies import Policy
from pearl.runtime.environment import EnvironmentRuntime
from pearl.runtime.episode import EpisodeRunner
from pearl.spec import Partition, Scenario
from pearl.spec.trajectory import (
    PolicyReference,
    RunManifest,
    Trajectory,
    canonical_json_bytes,
    policy_reference,
)

RuntimeFactory = Callable[[], EnvironmentRuntime]


@dataclass(frozen=True)
class RunBundle:
    """In-memory Run ready for durable artifact storage."""

    manifest: RunManifest
    scenarios: tuple[Scenario, ...]
    trajectories: tuple[Trajectory, ...]


class BatchRunner:
    """Execute an ordered Scenario batch with a fresh runtime per Episode."""

    def __init__(self, episode_runner: EpisodeRunner | None = None) -> None:
        self._episode_runner = episode_runner or EpisodeRunner()

    async def run(
        self,
        runtime_factory: RuntimeFactory,
        policy: Policy,
        scenarios: Sequence[Scenario],
        *,
        partition: Partition,
        sampling_seed: int,
        reference: PolicyReference | None = None,
    ) -> RunBundle:
        fixed_scenarios = tuple(scenario.model_copy(deep=True) for scenario in scenarios)
        if not fixed_scenarios:
            raise ValueError("A Run requires at least one Scenario")
        if sampling_seed < 0:
            raise ValueError("sampling_seed must be non-negative")
        if any(scenario.partition != partition for scenario in fixed_scenarios):
            raise ValueError("Every Scenario in a Run must match its fixed partition")
        if len({scenario.id for scenario in fixed_scenarios}) != len(fixed_scenarios):
            raise ValueError("Scenario IDs must be unique within a Run")

        first_runtime = runtime_factory()
        environment_id = first_runtime.spec.metadata.id
        environment_version = first_runtime.spec.metadata.version
        fixed_policy = reference or policy_reference(policy.name, policy.version)
        for scenario in fixed_scenarios:
            first_runtime.spec.validate_scenario(scenario)

        trajectories: list[Trajectory] = []
        for index, scenario in enumerate(fixed_scenarios):
            runtime = first_runtime if index == 0 else runtime_factory()
            if (
                runtime.spec.metadata.id != environment_id
                or runtime.spec.metadata.version != environment_version
            ):
                raise ValueError("runtime_factory must return one fixed Environment version")
            trajectories.append(
                await self._episode_runner.run(runtime, policy, scenario, fixed_policy)
            )

        fixed_trajectories = tuple(trajectories)
        run_id = run_id_for(
            environment_id=environment_id,
            environment_version=environment_version,
            partition=partition,
            sampling_seed=sampling_seed,
            scenarios=fixed_scenarios,
            policy=fixed_policy,
            trajectories=fixed_trajectories,
        )
        manifest = RunManifest(
            run_id=run_id,
            environment_id=environment_id,
            environment_version=environment_version,
            partition=partition,
            sampling_seed=sampling_seed,
            scenario_ids=tuple(scenario.id for scenario in fixed_scenarios),
            policy=fixed_policy,
        )
        return RunBundle(manifest, fixed_scenarios, fixed_trajectories)


async def run_batch(
    runtime_factory: RuntimeFactory,
    policy: Policy,
    scenarios: Sequence[Scenario],
    *,
    partition: Partition,
    sampling_seed: int,
    reference: PolicyReference | None = None,
) -> RunBundle:
    """Convenience wrapper around the deterministic ordered BatchRunner."""
    return await BatchRunner().run(
        runtime_factory,
        policy,
        scenarios,
        partition=partition,
        sampling_seed=sampling_seed,
        reference=reference,
    )


def run_id_for(
    *,
    environment_id: str,
    environment_version: int,
    partition: Partition,
    sampling_seed: int,
    scenarios: Sequence[Scenario],
    policy: PolicyReference,
    trajectories: Sequence[Trajectory],
) -> str:
    """Derive a stable Run ID from the complete immutable evidence bundle."""
    identity = {
        "artifact_schema_version": "1.0",
        "environment_id": environment_id,
        "environment_version": environment_version,
        "partition": partition.value,
        "sampling_seed": sampling_seed,
        "scenarios": tuple(scenarios),
        "policy": policy,
        "trajectories": tuple(trajectories),
    }
    digest = hashlib.sha256(canonical_json_bytes(identity)).hexdigest()[:16]
    return f"run_{digest}"
