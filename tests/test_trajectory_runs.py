from __future__ import annotations

import asyncio
from dataclasses import replace
from pathlib import Path

import pytest
from pydantic import ValidationError

from pearl.environments.enterprise25 import (
    create_e01_baseline_policy,
    create_e01_runtime,
)
from pearl.runtime.artifacts import ArtifactStoreError, JsonlArtifactStore
from pearl.runtime.episode import EpisodeRunner, run_episode
from pearl.runtime.runner import run_batch
from pearl.scenarios import load_scenario_distribution
from pearl.spec import Partition
from pearl.spec.trajectory import Step, Trajectory


def _search_scenarios(n: int = 50, seed: int = 42):
    sampled = load_scenario_distribution("E01").sample(n, seed)
    return tuple(item for item in sampled if item.partition == Partition.SEARCH)


def _trajectory():
    return asyncio.run(
        run_episode(
            create_e01_runtime(), create_e01_baseline_policy(), _search_scenarios()[0]
        )
    )


def _bundle():
    return asyncio.run(
        run_batch(
            create_e01_runtime,
            create_e01_baseline_policy(),
            _search_scenarios(),
            partition=Partition.SEARCH,
            sampling_seed=42,
        )
    )


def test_episode_runner_captures_complete_canonical_trace() -> None:
    trajectory = _trajectory()

    assert trajectory.environment_id == "enterprise25.E01"
    assert trajectory.policy.name == "baseline"
    assert trajectory.termination_reason in {"resolved", "escalated"}
    assert [step.index for step in trajectory.steps] == [0, 1, 2]
    assert trajectory.steps[0].observation["id"] == "claim_intake"
    assert trajectory.steps[0].tool_call == {
        "tool_id": "claims_api",
        "arguments": {},
    }
    assert trajectory.steps[1].tool_call == {
        "tool_id": "policy_store",
        "arguments": {},
    }
    assert trajectory.steps[2].tool_call is None
    assert trajectory.steps[-1].state_after["review_phase"] == "complete"


def test_trajectory_is_deeply_immutable() -> None:
    trajectory = _trajectory()

    with pytest.raises(ValidationError):
        trajectory.termination_reason = "changed"
    with pytest.raises(TypeError, match="immutable"):
        trajectory.runtime_metadata["partition"] = "confirmation"
    with pytest.raises(TypeError, match="immutable"):
        trajectory.steps[0].state_before["review_phase"] = "changed"
    with pytest.raises(TypeError, match="immutable"):
        trajectory.steps[0].tool_call["tool_id"] = "changed"  # type: ignore[index]


def test_trajectory_rejects_broken_state_continuity() -> None:
    trajectory = _trajectory()
    broken_second = trajectory.steps[1].model_copy(
        update={"state_before": {"review_phase": "wrong"}}
    )

    with pytest.raises(ValidationError, match="preceding Step"):
        Trajectory.model_validate(
            {
                **trajectory.model_dump(),
                "steps": (trajectory.steps[0], broken_second, trajectory.steps[2]),
            }
        )


def test_trajectory_rejects_an_id_that_does_not_match_its_content() -> None:
    trajectory = _trajectory()

    with pytest.raises(ValidationError, match="trajectory_id"):
        Trajectory.model_validate(
            {**trajectory.model_dump(), "termination_reason": "different"}
        )


def test_step_rejects_non_json_or_non_finite_evidence() -> None:
    trajectory = _trajectory()
    payload = trajectory.steps[0].model_dump()

    with pytest.raises(ValidationError, match="finite JSON"):
        Step.model_validate({**payload, "tool_result": {"score": float("nan")}})
    with pytest.raises(ValidationError, match="finite JSON"):
        Step.model_validate({**payload, "tool_result": {"bad": object()}})


def test_injected_clock_records_policy_and_runtime_latency() -> None:
    ticks = iter((1_000_000_000, 1_004_900_000, 2_000_000_000, 2_008_000_000,
                  3_000_000_000, 3_012_000_000))
    runner = EpisodeRunner(clock_ns=lambda: next(ticks))

    trajectory = asyncio.run(
        runner.run(
            create_e01_runtime(), create_e01_baseline_policy(), _search_scenarios()[0]
        )
    )

    assert [step.latency_ms for step in trajectory.steps] == [4, 8, 12]


def test_batch_runner_fixes_order_partition_and_content_identity() -> None:
    first = _bundle()
    second = _bundle()

    assert first == second
    assert first.manifest.run_id == "run_e2d9b96cae039fe3"
    assert first.manifest.scenario_ids == tuple(item.id for item in first.scenarios)
    assert tuple(item.scenario_id for item in first.trajectories) == (
        first.manifest.scenario_ids
    )
    assert len(first.scenarios) == 32
    assert all(item.runtime_metadata["partition"] == "search" for item in first.trajectories)


def test_batch_runner_rejects_partition_mixing() -> None:
    sampled = load_scenario_distribution("E01").sample(50, 42)

    with pytest.raises(ValueError, match="fixed partition"):
        asyncio.run(
            run_batch(
                create_e01_runtime,
                create_e01_baseline_policy(),
                sampled,
                partition=Partition.SEARCH,
                sampling_seed=42,
            )
        )


def test_jsonl_artifact_store_round_trips_and_is_idempotent(tmp_path: Path) -> None:
    bundle = _bundle()
    store = JsonlArtifactStore(tmp_path)

    path = store.write(bundle)
    same_path = store.write(bundle)
    restored = store.read(bundle.manifest.run_id)

    assert path == same_path
    assert restored == bundle
    assert sorted(item.name for item in path.iterdir()) == [
        "manifest.json",
        "scenarios.jsonl",
        "trajectories.jsonl",
    ]
    assert len((path / "scenarios.jsonl").read_text().splitlines()) == 32
    assert len((path / "trajectories.jsonl").read_text().splitlines()) == 32


def test_artifact_store_never_overwrites_a_conflicting_run(tmp_path: Path) -> None:
    bundle = _bundle()
    store = JsonlArtifactStore(tmp_path)
    path = store.write(bundle)
    (path / "trajectories.jsonl").write_text("tampered\n", encoding="utf-8")

    with pytest.raises(ArtifactStoreError, match="differs"):
        store.write(bundle)
    assert (path / "trajectories.jsonl").read_text(encoding="utf-8") == "tampered\n"


def test_artifact_store_detects_scenario_content_tampering(tmp_path: Path) -> None:
    bundle = _bundle()
    store = JsonlArtifactStore(tmp_path)
    path = store.write(bundle)
    scenario_path = path / "scenarios.jsonl"
    lines = scenario_path.read_text(encoding="utf-8").splitlines()
    lines[0] = lines[0].replace('"claim_amount":7200', '"claim_amount":7201')
    scenario_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    with pytest.raises(ArtifactStoreError, match="Run ID"):
        store.read(bundle.manifest.run_id)


def test_artifact_store_rejects_bundle_mismatch_before_writing(tmp_path: Path) -> None:
    bundle = _bundle()
    invalid = replace(
        bundle,
        manifest=bundle.manifest.model_copy(
            update={"scenario_ids": tuple(reversed(bundle.manifest.scenario_ids))}
        ),
    )

    with pytest.raises(ArtifactStoreError, match="manifest order"):
        JsonlArtifactStore(tmp_path).write(invalid)
    assert tuple(tmp_path.iterdir()) == ()
