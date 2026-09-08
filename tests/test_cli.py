import json
from pathlib import Path

from typer.testing import CliRunner

from pearl.cli.app import app

runner = CliRunner()


def test_help() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Environment-centric experimentation" in result.output


def test_version() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.output.strip() == "pearl 0.1.0.dev0"


def test_run_exit_gate_produces_inspectable_artifacts(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "run",
            "E01",
            "--policy",
            "baseline",
            "--partition",
            "search",
            "--output",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0, result.output
    assert "EPISODES: 32 (search)" in result.output
    run_directories = tuple(tmp_path.glob("run_*"))
    assert len(run_directories) == 1
    run_directory = run_directories[0]
    manifest = json.loads((run_directory / "manifest.json").read_text())
    scenarios = (run_directory / "scenarios.jsonl").read_text().splitlines()
    trajectories = (run_directory / "trajectories.jsonl").read_text().splitlines()
    assert manifest["run_id"] == run_directory.name
    assert manifest["partition"] == "search"
    assert manifest["policy"]["name"] == "baseline"
    assert len(scenarios) == len(trajectories) == 32
    assert all(json.loads(line)["partition"] == "search" for line in scenarios)


def test_run_rejects_unavailable_policy_without_artifacts(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["run", "E01", "--policy", "unknown", "--output", str(tmp_path)],
    )

    assert result.exit_code == 1
    assert 'Policy "unknown" is not available' in result.output
    assert tuple(tmp_path.iterdir()) == ()
