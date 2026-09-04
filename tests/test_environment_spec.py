from __future__ import annotations

from copy import deepcopy
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError
from typer.testing import CliRunner

from pearl.cli.app import app
from pearl.spec import (
    EnvironmentSpec,
    Scenario,
    SpecLoadError,
    load_environment_bundle,
    load_environment_spec,
)


def valid_environment() -> dict:
    return {
        "pearl_spec_version": "1.0",
        "metadata": {
            "id": "enterprise25.E01",
            "name": "Claims Dispute Resolution",
            "version": 1,
            "vertical": "fsi_insurance",
            "workflow_archetype": "support_resolution",
            "tags": ["gold"],
        },
        "objective": {
            "task": "resolve_claim_dispute",
            "business_goal": "Produce an accurate, policy-grounded recommendation.",
        },
        "actors": [
            {"id": "claimant", "name": "Claimant", "role": "requests resolution"}
        ],
        "state_schema": {
            "claim_status": {
                "type": "string",
                "description": "Current claim status.",
                "default": "open",
            },
            "evidence_complete": {
                "type": "boolean",
                "description": "Whether required evidence is complete.",
                "default": False,
            },
        },
        "observations": [
            {
                "id": "claim_summary",
                "description": "Current claim state.",
                "state_fields": ["claim_status", "evidence_complete"],
            }
        ],
        "actions": [
            {
                "id": "retrieve_policy",
                "description": "Retrieve the controlling policy.",
                "tool_id": "policy_search",
                "observation_id": "claim_summary",
            }
        ],
        "tools": [
            {
                "id": "policy_search",
                "description": "Search authoritative policy documents.",
            }
        ],
        "constraints": [
            {
                "id": "human_approval",
                "description": "A human approves final payment.",
                "action_ids": ["retrieve_policy"],
            }
        ],
        "ground_truth": [
            {
                "id": "resolved_claim",
                "description": "A resolved claim is closed.",
                "state_values": {"claim_status": "closed"},
            }
        ],
        "termination": {
            "max_steps": 12,
            "success_conditions": ["claim_resolved"],
            "failure_conditions": ["step_limit"],
        },
        "evaluation": {
            "dimensions": [
                {
                    "id": "task_success",
                    "description": "Whether the claim was resolved correctly.",
                    "metric_type": "binary",
                }
            ],
            "evaluators": [
                {"id": "deterministic_success", "dimension": "task_success"}
            ],
            "hard_gates": [
                {"metric": "task_success", "operator": "gte", "value": 0.8}
            ],
        },
        "provenance": {
            "objective": {},
            "actrw": {
                "agency": {},
                "context": {},
                "truth": {},
                "risk": {},
                "workflow": {},
            },
        },
    }


def build(changer) -> EnvironmentSpec:
    payload = deepcopy(valid_environment())
    changer(payload)
    return EnvironmentSpec.model_validate(payload)


def test_valid_environment_spec() -> None:
    spec = EnvironmentSpec.model_validate(valid_environment())

    assert spec.metadata.id == "enterprise25.E01"
    assert spec.pearl_spec_version == "1.0"
    assert spec.state_schema["claim_status"].default == "open"


def test_environment_spec_is_immutable() -> None:
    spec = EnvironmentSpec.model_validate(valid_environment())

    with pytest.raises(ValidationError):
        spec.metadata.version = 2


def test_invalid_schema_version_is_rejected() -> None:
    with pytest.raises(ValidationError, match="pearl_spec_version"):
        build(lambda payload: payload.update(pearl_spec_version="2.0"))


@pytest.mark.parametrize(
    "collection",
    ["actors", "observations", "actions", "tools", "constraints", "ground_truth"],
)
def test_duplicate_component_ids_are_rejected(collection: str) -> None:
    def duplicate(payload: dict) -> None:
        payload[collection].append(deepcopy(payload[collection][0]))

    expected = "ground-truth" if collection == "ground_truth" else collection.rstrip("s")
    with pytest.raises(ValidationError, match=f"duplicate .*{expected}"):
        build(duplicate)


def test_duplicate_dimension_ids_are_rejected() -> None:
    def duplicate(payload: dict) -> None:
        payload["evaluation"]["dimensions"].append(
            deepcopy(payload["evaluation"]["dimensions"][0])
        )

    with pytest.raises(ValidationError, match="duplicate evaluation dimension"):
        build(duplicate)


def test_missing_tool_reference_is_actionable() -> None:
    def break_reference(payload: dict) -> None:
        payload["actions"][0]["tool_id"] = "missing_tool"

    with pytest.raises(ValidationError, match='references tool "missing_tool"'):
        build(break_reference)


def test_missing_observation_reference_is_actionable() -> None:
    def break_reference(payload: dict) -> None:
        payload["actions"][0]["observation_id"] = "missing_observation"

    with pytest.raises(ValidationError, match='references observation "missing_observation"'):
        build(break_reference)


def test_observation_state_reference_is_validated() -> None:
    def break_reference(payload: dict) -> None:
        payload["observations"][0]["state_fields"].append("missing_state")

    with pytest.raises(ValidationError, match='references state field "missing_state"'):
        build(break_reference)


def test_constraint_action_reference_is_validated() -> None:
    def break_reference(payload: dict) -> None:
        payload["constraints"][0]["action_ids"] = ["missing_action"]

    with pytest.raises(ValidationError, match='references action "missing_action"'):
        build(break_reference)


def test_evaluator_dimension_reference_is_validated() -> None:
    def break_reference(payload: dict) -> None:
        payload["evaluation"]["evaluators"][0]["dimension"] = "grounding"

    with pytest.raises(ValidationError, match='references dimension "grounding"'):
        build(break_reference)


def test_hard_gate_metric_reference_is_validated() -> None:
    def break_reference(payload: dict) -> None:
        payload["evaluation"]["hard_gates"][0]["metric"] = "grounding"

    with pytest.raises(ValidationError, match='Hard Gate references metric "grounding"'):
        build(break_reference)


def test_nonpositive_max_steps_is_rejected() -> None:
    def break_steps(payload: dict) -> None:
        payload["termination"]["max_steps"] = 0

    with pytest.raises(ValidationError, match="max_steps"):
        build(break_steps)


def test_invalid_state_default_is_rejected() -> None:
    def break_default(payload: dict) -> None:
        payload["state_schema"]["evidence_complete"]["default"] = "yes"

    with pytest.raises(ValidationError, match="does not match declared state type"):
        build(break_default)


def test_explicit_null_state_default_is_rejected() -> None:
    def break_default(payload: dict) -> None:
        payload["state_schema"]["claim_status"]["default"] = None

    with pytest.raises(ValidationError, match="does not match declared state type"):
        build(break_default)


def test_ground_truth_state_reference_is_validated() -> None:
    def break_reference(payload: dict) -> None:
        payload["ground_truth"][0]["state_values"] = {"missing_state": "closed"}

    with pytest.raises(ValidationError, match='references state field "missing_state"'):
        build(break_reference)


def test_ground_truth_state_type_is_validated() -> None:
    def break_type(payload: dict) -> None:
        payload["ground_truth"][0]["state_values"] = {"evidence_complete": "yes"}

    with pytest.raises(ValidationError, match="does not match declared type"):
        build(break_type)


def test_scenario_environment_reference_is_validated() -> None:
    spec = EnvironmentSpec.model_validate(valid_environment())
    scenario = Scenario(
        id="E01.S001",
        environment_id="enterprise25.E02",
        seed=1,
        initial_state={},
    )

    with pytest.raises(ValueError, match='references environment "enterprise25.E02"'):
        spec.validate_scenario(scenario)


def test_scenario_state_and_tool_references_are_validated() -> None:
    spec = EnvironmentSpec.model_validate(valid_environment())
    scenario = Scenario(
        id="E01.S001",
        environment_id="enterprise25.E01",
        seed=1,
        initial_state={"unknown": "value"},
        tool_conditions={"missing_tool": "healthy"},
    )

    with pytest.raises(ValueError, match="unknown initial-state fields"):
        spec.validate_scenario(scenario)


def test_scenario_tool_reference_is_validated() -> None:
    spec = EnvironmentSpec.model_validate(valid_environment())
    scenario = Scenario(
        id="E01.S001",
        environment_id="enterprise25.E01",
        seed=1,
        initial_state={},
        tool_conditions={"missing_tool": "healthy"},
    )

    with pytest.raises(ValueError, match="conditions for unknown tools"):
        spec.validate_scenario(scenario)


def test_scenario_missing_required_state_is_validated() -> None:
    payload = valid_environment()
    del payload["state_schema"]["claim_status"]["default"]
    spec = EnvironmentSpec.model_validate(payload)
    scenario = Scenario(
        id="E01.S001",
        environment_id="enterprise25.E01",
        seed=1,
        initial_state={},
    )

    with pytest.raises(ValueError, match="missing required initial-state fields"):
        spec.validate_scenario(scenario)


def test_scenario_state_types_are_validated() -> None:
    spec = EnvironmentSpec.model_validate(valid_environment())
    scenario = Scenario(
        id="E01.S001",
        environment_id="enterprise25.E01",
        seed=1,
        initial_state={"evidence_complete": "yes"},
    )

    with pytest.raises(ValueError, match="does not match declared type"):
        spec.validate_scenario(scenario)


def test_loader_reports_missing_required_field(tmp_path: Path) -> None:
    payload = valid_environment()
    del payload["objective"]
    path = tmp_path / "environment.yaml"
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")

    with pytest.raises(SpecLoadError, match='missing required field "objective"'):
        load_environment_spec(path)


def test_loader_reports_malformed_ground_truth(tmp_path: Path) -> None:
    payload = valid_environment()
    del payload["ground_truth"][0]["description"]
    path = tmp_path / "environment.yaml"
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")

    with pytest.raises(SpecLoadError, match="ground_truth.0.description"):
        load_environment_spec(path)


def test_loader_rejects_non_mapping_yaml(tmp_path: Path) -> None:
    path = tmp_path / "environment.yaml"
    path.write_text("- not\n- a\n- mapping\n", encoding="utf-8")

    with pytest.raises(SpecLoadError, match="must contain a YAML mapping"):
        load_environment_spec(path)


def test_environment_directory_loads_and_validates_scenarios(tmp_path: Path) -> None:
    environment_dir = tmp_path / "E01"
    scenarios_dir = environment_dir / "scenarios"
    scenarios_dir.mkdir(parents=True)
    (environment_dir / "environment.yaml").write_text(
        yaml.safe_dump(valid_environment()), encoding="utf-8"
    )
    scenario = {
        "id": "E01.S001",
        "environment_id": "enterprise25.E01",
        "seed": 1,
        "initial_state": {"claim_status": "open", "evidence_complete": False},
        "tool_conditions": {"policy_search": "healthy"},
    }
    (scenarios_dir / "S001.yaml").write_text(yaml.safe_dump(scenario), encoding="utf-8")

    spec, scenarios = load_environment_bundle(environment_dir)

    assert spec.metadata.id == "enterprise25.E01"
    assert [item.id for item in scenarios] == ["E01.S001"]


def test_validate_cli_accepts_valid_environment(tmp_path: Path) -> None:
    path = tmp_path / "environment.yaml"
    path.write_text(yaml.safe_dump(valid_environment()), encoding="utf-8")

    result = CliRunner().invoke(app, ["validate", str(path)])

    assert result.exit_code == 0
    assert "VALID: enterprise25.E01 v1" in result.output


def test_validate_cli_prints_actionable_error(tmp_path: Path) -> None:
    payload = valid_environment()
    payload["actions"][0]["tool_id"] = "missing_tool"
    path = tmp_path / "environment.yaml"
    path.write_text(yaml.safe_dump(payload), encoding="utf-8")

    result = CliRunner().invoke(app, ["validate", str(path)])

    assert result.exit_code == 1
    assert 'references tool "missing_tool"' in result.output
