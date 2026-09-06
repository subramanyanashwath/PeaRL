"""Enterprise-25 Registry Environment schema and loader."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from pearl.spec.loader import SpecLoadError
from pearl.spec.paths import canonical_data_path

Vertical = Literal[
    "fsi_insurance",
    "healthcare",
    "retail",
    "manufacturing",
    "transportation_logistics",
]
WorkflowArchetype = Literal[
    "support_resolution",
    "research_investigation",
    "compliance_review",
    "operations_exceptions",
    "planning_decision",
]


class RegistryEnvironment(BaseModel):
    """Named environment slot; no executable runtime is implied."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str = Field(pattern=r"^enterprise25\.E\d{2}$")
    name: str = Field(min_length=1)
    vertical: Vertical
    workflow_archetype: WorkflowArchetype
    objective: str = Field(min_length=1)
    primary_capability_stresses: tuple[str, ...] = Field(min_length=1)
    expected_failure_families: tuple[str, ...] = Field(min_length=1)
    maturity: Literal["registry"] = "registry"


class Enterprise25Registry(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    pearl_registry_version: Literal["1.0"]
    environments: tuple[RegistryEnvironment, ...] = Field(min_length=25, max_length=25)

    @model_validator(mode="after")
    def validate_matrix(self) -> Enterprise25Registry:
        expected_ids = {f"enterprise25.E{index:02d}" for index in range(1, 26)}
        actual_ids = {environment.id for environment in self.environments}
        if len(actual_ids) != len(self.environments):
            raise ValueError("Enterprise-25 registry contains duplicate environment IDs.")
        if actual_ids != expected_ids:
            missing = ", ".join(sorted(expected_ids - actual_ids)) or "none"
            unexpected = ", ".join(sorted(actual_ids - expected_ids)) or "none"
            raise ValueError(
                "Enterprise-25 registry IDs must be E01 through E25; "
                f"missing: {missing}; unexpected: {unexpected}."
            )

        combinations = {
            (environment.vertical, environment.workflow_archetype)
            for environment in self.environments
        }
        if len(combinations) != 25:
            raise ValueError(
                "Enterprise-25 registry must contain each vertical/workflow "
                "archetype combination exactly once."
            )
        return self


def default_registry_path() -> Path:
    """Return the canonical registry in a source checkout or installed wheel."""
    relative = Path("environments") / "enterprise25" / "registry.yaml"
    return canonical_data_path(relative)


def load_registry(path: str | Path | None = None) -> Enterprise25Registry:
    target = Path(path) if path is not None else default_registry_path()
    if not target.is_file():
        raise SpecLoadError(f'Enterprise-25 registry file "{target}" does not exist.')
    try:
        payload = yaml.safe_load(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeError) as exc:
        raise SpecLoadError(f'Could not read registry file "{target}": {exc}') from exc
    except yaml.YAMLError as exc:
        raise SpecLoadError(f'Could not parse registry YAML in "{target}": {exc}') from exc
    try:
        return Enterprise25Registry.model_validate(payload)
    except ValidationError as exc:
        first = exc.errors()[0]
        location = ".".join(str(part) for part in first["loc"] if part != "function-after")
        detail = str(first["msg"])
        suffix = f' at field "{location}"' if location else ""
        raise SpecLoadError(f"Enterprise-25 registry is invalid{suffix}: {detail}.") from exc
