"""YAML loading with actionable PeaRL validation errors."""

from __future__ import annotations

from pathlib import Path
from typing import TypeVar

import yaml
from pydantic import BaseModel, ValidationError

from pearl.spec.environment import EnvironmentSpec
from pearl.spec.scenario import Scenario

ModelT = TypeVar("ModelT", bound=BaseModel)


class SpecLoadError(ValueError):
    """A human-actionable specification loading or validation failure."""


def load_environment_spec(path: str | Path) -> EnvironmentSpec:
    return _load_model(path, EnvironmentSpec, "Environment specification")


def load_scenario(path: str | Path) -> Scenario:
    return _load_model(path, Scenario, "Scenario")


def load_environment_bundle(path: str | Path) -> tuple[EnvironmentSpec, tuple[Scenario, ...]]:
    """Load an environment YAML file or an environment directory with Scenarios."""
    target = Path(path)
    if target.is_dir():
        environment_path = target / "environment.yaml"
        scenario_paths = sorted((target / "scenarios").glob("*.yaml"))
    else:
        environment_path = target
        scenario_paths = []

    environment = load_environment_spec(environment_path)
    scenarios = tuple(load_scenario(scenario_path) for scenario_path in scenario_paths)
    for scenario in scenarios:
        try:
            environment.validate_scenario(scenario)
        except ValueError as exc:
            raise SpecLoadError(str(exc)) from exc
    return environment, scenarios


def _load_model(path: str | Path, model: type[ModelT], label: str) -> ModelT:
    target = Path(path)
    if not target.is_file():
        raise SpecLoadError(f'{label} file "{target}" does not exist.')

    try:
        payload = yaml.safe_load(target.read_text(encoding="utf-8"))
    except (OSError, UnicodeError) as exc:
        raise SpecLoadError(f'Could not read {label.lower()} file "{target}": {exc}') from exc
    except yaml.YAMLError as exc:
        raise SpecLoadError(f'Could not parse YAML in "{target}": {exc}') from exc

    if not isinstance(payload, dict):
        raise SpecLoadError(f'{label} file "{target}" must contain a YAML mapping.')

    try:
        return model.model_validate(payload)
    except ValidationError as exc:
        raise SpecLoadError(_format_validation_error(label, exc)) from exc


def _format_validation_error(label: str, error: ValidationError) -> str:
    first = error.errors()[0]
    location = ".".join(str(part) for part in first["loc"] if part != "function-after")
    message = str(first["msg"])
    if first["type"] == "missing":
        return f'{label} is missing required field "{location}".'
    if location:
        return f'{label} has invalid field "{location}": {message}.'
    return f"{label} is invalid: {message}."
