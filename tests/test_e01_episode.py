from __future__ import annotations

import asyncio

from pearl.environments.enterprise25 import (
    create_e01_baseline_policy,
    create_e01_runtime,
)
from pearl.runtime.episode import run_episode
from pearl.scenarios import load_scenario_distribution


def test_complete_multistep_e01_episode_executes() -> None:
    scenario = load_scenario_distribution("E01").sample(1, 42)[0]

    trajectory = asyncio.run(
        run_episode(create_e01_runtime(), create_e01_baseline_policy(), scenario)
    )

    assert len(trajectory.steps) == 3
    assert [step.index for step in trajectory.steps] == [0, 1, 2]
    assert trajectory.termination_reason in {"resolved", "escalated"}
    assert trajectory.steps[-1].state_after["review_phase"] == "complete"


def test_e01_episode_is_deterministic_for_same_scenario_and_policy() -> None:
    scenario = load_scenario_distribution("E01").sample(1, 42)[0]

    first = asyncio.run(
        run_episode(create_e01_runtime(), create_e01_baseline_policy(), scenario)
    )
    second = asyncio.run(
        run_episode(create_e01_runtime(), create_e01_baseline_policy(), scenario)
    )

    assert first == second


def test_all_day3_exit_gate_scenarios_execute_to_termination() -> None:
    scenarios = load_scenario_distribution("E01").sample(50, 42)

    trajectories = [
        asyncio.run(
            run_episode(create_e01_runtime(), create_e01_baseline_policy(), scenario)
        )
        for scenario in scenarios
    ]

    assert all(len(trajectory.steps) == 3 for trajectory in trajectories)
    assert all(trajectory.termination_reason for trajectory in trajectories)
