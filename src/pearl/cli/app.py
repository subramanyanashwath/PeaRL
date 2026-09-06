"""PeaRL command-line entry point."""

from __future__ import annotations

from pathlib import Path

import typer

from pearl import __version__
from pearl.scenarios import load_scenario_distribution
from pearl.spec import (
    SpecLoadError,
    default_registry_path,
    load_environment_bundle,
    load_registry,
)

app = typer.Typer(
    name="pearl",
    help="Environment-centric experimentation and improvement for AI agents.",
    no_args_is_help=True,
)
registry_app = typer.Typer(help="Inspect the Enterprise-25 environment registry.")
app.add_typer(registry_app, name="registry")


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"pearl {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        callback=_version_callback,
        is_eager=True,
        help="Show the PeaRL version and exit.",
    ),
) -> None:
    """Inspect and run PeaRL experiments."""


@app.command()
def validate(path: Path) -> None:
    """Validate an EnvironmentSpec file or environment directory."""
    try:
        environment, scenarios = load_environment_bundle(path)
    except SpecLoadError as exc:
        typer.echo(f"INVALID: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(
        f"VALID: {environment.metadata.id} v{environment.metadata.version} "
        f"({len(scenarios)} scenarios)"
    )


@app.command()
def sample(
    environment: str = typer.Argument(help="Environment ID, for example E01."),
    n: int = typer.Option(50, "--n", min=1, help="Number of Scenarios to emit."),
    seed: int = typer.Option(0, "--seed", min=0, help="Non-negative sampling seed."),
) -> None:
    """Emit deterministic generated Scenarios as JSON Lines."""
    try:
        scenarios = load_scenario_distribution(environment).sample(n, seed)
    except (SpecLoadError, ValueError) as exc:
        typer.echo(f"INVALID: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    for scenario in scenarios:
        typer.echo(scenario.model_dump_json())


@registry_app.command("list")
def list_registry(
    registry: Path = typer.Option(
        default_registry_path(),
        "--registry",
        help="Path to the Enterprise-25 registry YAML file.",
    ),
) -> None:
    """List all Enterprise-25 Registry Environments."""
    try:
        entries = load_registry(registry).environments
    except SpecLoadError as exc:
        typer.echo(f"INVALID: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    for environment in entries:
        typer.echo(
            f"{environment.id}  {environment.name}  "
            f"[{environment.vertical} / {environment.workflow_archetype}]"
        )
    typer.echo(f"\n{len(entries)} Registry Environments")


if __name__ == "__main__":  # pragma: no cover
    app()
