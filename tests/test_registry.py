from __future__ import annotations

from copy import deepcopy

import pytest
from pydantic import ValidationError
from typer.testing import CliRunner

from pearl.cli.app import app
from pearl.spec import Enterprise25Registry, default_registry_path, load_registry

EXPECTED_NAMES = {
    "enterprise25.E01": "Claims Dispute Resolution",
    "enterprise25.E02": "Prior Authorization Appeal",
    "enterprise25.E03": "Store Escalation Resolution",
    "enterprise25.E04": "Supplier Quality Dispute",
    "enterprise25.E05": "Delivery Exception Resolution",
    "enterprise25.E06": "Credit Deterioration Investigation",
    "enterprise25.E07": "Utilization Anomaly Investigation",
    "enterprise25.E08": "Merchandising Performance Investigation",
    "enterprise25.E09": "Quality Root-Cause Investigation",
    "enterprise25.E10": "Network Delay Root-Cause Investigation",
    "enterprise25.E11": "KYC / AML Case Review",
    "enterprise25.E12": "Medical-Necessity Compliance Review",
    "enterprise25.E13": "Pricing & Promotion Compliance Audit",
    "enterprise25.E14": "Supplier Regulatory Documentation Review",
    "enterprise25.E15": "Customs & Shipping Documentation Review",
    "enterprise25.E16": "Account Servicing Exception",
    "enterprise25.E17": "Claims Adjudication Exception",
    "enterprise25.E18": "Inventory Replenishment Exception",
    "enterprise25.E19": "Production Disruption Recovery",
    "enterprise25.E20": "Shipment Routing Exception",
    "enterprise25.E21": "Credit Workout Planning",
    "enterprise25.E22": "Care Coordination Planning",
    "enterprise25.E23": "Assortment & Inventory Planning",
    "enterprise25.E24": "Production Capacity Planning",
    "enterprise25.E25": "Network Capacity & Route Planning",
}


def test_canonical_registry_contains_all_25_environments() -> None:
    registry = load_registry()

    assert len(registry.environments) == 25
    assert {item.id: item.name for item in registry.environments} == EXPECTED_NAMES


def test_registry_covers_each_matrix_cell_once() -> None:
    registry = load_registry()
    combinations = {
        (item.vertical, item.workflow_archetype) for item in registry.environments
    }

    assert len(combinations) == 25


def test_registry_entries_have_required_discovery_content() -> None:
    registry = load_registry()

    assert all(item.objective for item in registry.environments)
    assert all(item.primary_capability_stresses for item in registry.environments)
    assert all(item.expected_failure_families for item in registry.environments)
    assert all(item.maturity == "registry" for item in registry.environments)


def test_default_registry_path_exists() -> None:
    assert default_registry_path().is_file()


def test_duplicate_registry_id_is_rejected() -> None:
    payload = load_registry().model_dump(mode="json")
    broken = deepcopy(payload)
    broken["environments"][1]["id"] = "enterprise25.E01"

    with pytest.raises(ValidationError, match="duplicate environment IDs"):
        Enterprise25Registry.model_validate(broken)


def test_duplicate_matrix_cell_is_rejected() -> None:
    payload = load_registry().model_dump(mode="json")
    broken = deepcopy(payload)
    broken["environments"][1]["vertical"] = broken["environments"][0]["vertical"]
    broken["environments"][1]["workflow_archetype"] = broken["environments"][0][
        "workflow_archetype"
    ]

    with pytest.raises(ValidationError, match="each vertical/workflow"):
        Enterprise25Registry.model_validate(broken)


def test_registry_list_cli_returns_25() -> None:
    result = CliRunner().invoke(app, ["registry", "list"])

    assert result.exit_code == 0
    assert result.output.count("enterprise25.E") == 25
    assert "25 Registry Environments" in result.output
