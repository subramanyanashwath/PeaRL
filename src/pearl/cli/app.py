"""PeaRL command-line entry point."""

from __future__ import annotations

import asyncio
from pathlib import Path

import typer

from pearl import __version__
from pearl.environments.enterprise25 import (
    create_e01_baseline_policy,
    create_e01_evaluators,
    create_e01_runtime,
)
from pearl.evaluators import evaluate_run
from pearl.runtime.artifacts import ArtifactStoreError, JsonlArtifactStore
from pearl.runtime.runner import run_batch
from pearl.scenarios import load_scenario_distribution
from pearl.spec import (
    Partition,
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


@app.command("run")
def run_command(
    environment: str = typer.Argument(help="Environment ID, for example E01."),
    policy: str = typer.Option(..., "--policy", help="Policy name."),
    partition: Partition = typer.Option(
        Partition.SEARCH, "--partition", help="Evidence partition to execute."
    ),
    n: int = typer.Option(50, "--n", min=1, help="Size of the generated Scenario pool."),
    seed: int = typer.Option(42, "--seed", min=0, help="Scenario sampling seed."),
    output: Path = typer.Option(
        Path("runs"), "--output", help="Directory for immutable Run bundles."
    ),
) -> None:
    """Execute a Policy over one reproducible Scenario partition."""
    if environment.upper() != "E01":
        typer.echo(f'INVALID: EnvironmentRuntime "{environment}" is not available.', err=True)
        raise typer.Exit(code=1)
    if policy != "baseline":
        typer.echo(f'INVALID: Policy "{policy}" is not available for E01.', err=True)
        raise typer.Exit(code=1)

    try:
        sampled = load_scenario_distribution(environment).sample(n, seed)
        scenarios = tuple(item for item in sampled if item.partition == partition)
        bundle = asyncio.run(
            run_batch(
                create_e01_runtime,
                create_e01_baseline_policy(),
                scenarios,
                partition=partition,
                sampling_seed=seed,
            )
        )
        artifact_path = JsonlArtifactStore(output).write(bundle)
    except (ArtifactStoreError, SpecLoadError, ValueError) as exc:
        typer.echo(f"INVALID: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"RUN: {bundle.manifest.run_id}")
    typer.echo(f"EPISODES: {len(bundle.trajectories)} ({partition.value})")
    typer.echo(f"ARTIFACTS: {artifact_path}")


@app.command()
def evaluate(
    run_id: str = typer.Argument(help="Run ID to evaluate."),
    artifacts: Path = typer.Option(
        Path("runs"), "--artifacts", help="Directory containing Run bundles."
    ),
) -> None:
    """Attach a decomposed Evaluation Vector to every Episode in a Run."""
    store = JsonlArtifactStore(artifacts)
    try:
        run = store.read(run_id)
        if run.manifest.environment_id != "enterprise25.E01":
            raise ValueError(
                f'No Evaluator suite is available for "{run.manifest.environment_id}".'
            )
        evaluations = evaluate_run(run, create_e01_evaluators())
        evaluation_path = store.write_evaluations(evaluations)
    except (ArtifactStoreError, ValueError) as exc:
        typer.echo(f"INVALID: {exc}", err=True)
        raise typer.Exit(code=1) from exc

    typer.echo(f"EVALUATED: {run_id}")
    typer.echo(f"VECTORS: {len(evaluations.vectors)}")
    for index, result in enumerate(evaluations.vectors[0].results):
        dimension_results = tuple(vector.results[index] for vector in evaluations.vectors)
        mean_score = sum(item.score for item in dimension_results) / len(dimension_results)
        passed = sum(item.passed for item in dimension_results)
        typer.echo(
            f"{result.dimension}: {mean_score:.3f} "
            f"({passed}/{len(dimension_results)} passed)"
        )
    typer.echo(f"ARTIFACT: {evaluation_path}")


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
