from __future__ import annotations

import json
import random
from copy import deepcopy

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError
from typer.testing import CliRunner

from pearl.cli.app import app
from pearl.scenarios import (
    ChangePersona,
    DropStateField,
    ScenarioDistributionSpec,
    ScenarioMutator,
    SetStateValue,
    SetToolCondition,
    assign_partition,
    load_scenario_distribution,
)
from pearl.spec import Partition, Scenario, SeedScenario


def base_scenario() -> Scenario:
    return Scenario(
        id="E01.S001",
        environment_id="enterprise25.E01",
        seed=1,
        initial_state={"evidence": "present", "conflict": False},
        persona={"type": "calm"},
        tool_conditions={"policy_store": "healthy"},
        ground_truth={"expected_resolution": "approve"},
    )


def test_seed_scenario_requires_human_provenance() -> None:
    seed = SeedScenario(
        id="E01.seed.01",
        environment_id="enterprise25.E01",
        initial_state={},
        provenance={"author": "test_author"},
    )

    assert seed.provenance.author == "test_author"


def test_seed_scenario_rejects_generated_fields() -> None:
    with pytest.raises(ValidationError, match="seed"):
        SeedScenario.model_validate(
            {
                "id": "E01.seed.01",
                "environment_id": "enterprise25.E01",
                "seed": 42,
                "initial_state": {},
                "provenance": {"author": "test_author"},
            }
        )


@given(st.text(min_size=1))
def test_partition_assignment_is_deterministic(identity: str) -> None:
    assert assign_partition(identity) == assign_partition(identity)


def test_partition_assignment_exposes_all_three_labels() -> None:
    labels = {assign_partition(f"scenario-{index}") for index in range(100)}

    assert labels == set(Partition)


@pytest.mark.parametrize(
    ("mutator", "condition", "expected_parameter"),
    [
        (DropStateField(["evidence"]), "missing_evidence", "field"),
        (
            SetStateValue("conflict", [True], ground_truth_updates={"outcome": "escalate"}),
            "conflicting_truth",
            "value",
        ),
        (
            SetToolCondition(["policy_store"]),
            "tool_outage",
            "tool",
        ),
        (ChangePersona([{"type": "frustrated"}]), "changed_persona", "persona"),
    ],
)
def test_generic_mutators_are_bounded_immutable_and_provenance_bearing(
    mutator: ScenarioMutator, condition: str, expected_parameter: str
) -> None:
    original = base_scenario()
    before = deepcopy(original.model_dump())

    mutated = mutator.mutate(original, random.Random(42))

    assert original.model_dump() == before
    assert mutated.id == original.id
    assert mutated.seed == original.seed
    assert mutated.environment_id == original.environment_id
    assert condition in mutated.conditions
    assert len(mutated.provenance.mutations) == 1
    assert mutated.provenance.mutations[0].mutator == mutator.id
    assert expected_parameter in mutated.provenance.mutations[0].parameters


def test_ground_truth_repair_is_recorded_with_semantic_mutation() -> None:
    mutated = SetStateValue(
        "conflict", [True], ground_truth_updates={"expected_resolution": "escalate"}
    ).mutate(base_scenario(), random.Random(1))

    assert mutated.initial_state.root["conflict"] is True
    assert mutated.ground_truth["expected_resolution"] == "escalate"


def test_inapplicable_mutator_fails_explicitly() -> None:
    with pytest.raises(ValueError, match="not applicable"):
        DropStateField(["absent"]).mutate(base_scenario(), random.Random(1))


def test_distribution_configuration_rejects_invalid_bounds() -> None:
    with pytest.raises(ValidationError, match="min_mutations"):
        ScenarioDistributionSpec.model_validate(
            {
                "pearl_scenario_distribution_version": "1.0",
                "environment_id": "enterprise25.E01",
                "environment_version": 1,
                "version": "1.0",
                "min_mutations": 2,
                "max_mutations": 1,
                "mutators": [{"type": "change_persona", "personas": [{"type": "x"}]}],
            }
        )


def test_e01_distribution_has_first_seeds_and_four_generic_mutators() -> None:
    distribution = load_scenario_distribution("E01")

    assert len(distribution.seeds) == 4
    assert len(distribution.mutators) == 4
    assert {mutator.id for mutator in distribution.mutators} == {
        "drop_state_field",
        "set_state_value",
        "set_tool_condition",
        "change_persona",
    }


@given(seed=st.integers(min_value=0, max_value=2**32 - 1))
def test_e01_sampling_is_deterministic_for_any_seed(seed: int) -> None:
    distribution = load_scenario_distribution("enterprise25.E01")

    assert distribution.sample(12, seed) == distribution.sample(12, seed)


def test_sampling_is_prefix_stable_when_batch_size_changes() -> None:
    distribution = load_scenario_distribution("E01")

    assert distribution.sample(10, 42) == distribution.sample(50, 42)[:10]


def test_generated_scenarios_capture_complete_replay_provenance() -> None:
    scenarios = load_scenario_distribution("E01").sample(50, 42)

    assert len({scenario.id for scenario in scenarios}) == 50
    assert {scenario.partition for scenario in scenarios} == set(Partition)
    assert all(scenario.provenance.seed_scenario for scenario in scenarios)
    assert all(scenario.provenance.environment_version == 1 for scenario in scenarios)
    assert all(scenario.provenance.distribution_version == "1.0" for scenario in scenarios)
    assert all(1 <= len(scenario.provenance.mutations) <= 2 for scenario in scenarios)


def test_sample_cli_exit_gate_is_reproducible_json_lines() -> None:
    runner = CliRunner()

    first = runner.invoke(app, ["sample", "E01", "--n", "50", "--seed", "42"])
    second = runner.invoke(app, ["sample", "E01", "--n", "50", "--seed", "42"])

    assert first.exit_code == 0
    assert first.output == second.output
    payloads = [json.loads(line) for line in first.output.splitlines()]
    assert len(payloads) == 50
    assert {item["partition"] for item in payloads} == set(Partition)


def test_sample_cli_rejects_unknown_environment() -> None:
    result = CliRunner().invoke(app, ["sample", "E99", "--n", "1"])

    assert result.exit_code == 1
    assert "Could not resolve Environment" in result.output
