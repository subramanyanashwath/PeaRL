"""Atomic, file-first storage for canonical Run artifacts."""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

from pydantic import BaseModel, ValidationError

from pearl.runtime.runner import RunBundle, run_id_for
from pearl.spec import (
    EvaluationBundle,
    EvaluationVector,
    Scenario,
)
from pearl.spec.trajectory import RunManifest, Trajectory


class ArtifactStoreError(RuntimeError):
    """A Run artifact bundle could not be written or read safely."""


class JsonlArtifactStore:
    """Store each Run as an atomic, inspectable directory bundle."""

    def __init__(self, root: str | Path = "runs") -> None:
        self.root = Path(root)

    def write(self, bundle: RunBundle) -> Path:
        """Write a complete bundle once; exact reruns are idempotent."""
        self._validate_bundle(bundle)
        files = {
            "manifest.json": bundle.manifest.model_dump_json(indent=2) + "\n",
            "scenarios.jsonl": self._jsonl(bundle.scenarios),
            "trajectories.jsonl": self._jsonl(bundle.trajectories),
        }
        self.root.mkdir(parents=True, exist_ok=True)
        target = self.root / bundle.manifest.run_id
        if target.exists():
            self._assert_existing_matches(target, files)
            return target

        staging = Path(
            tempfile.mkdtemp(prefix=f".{bundle.manifest.run_id}.", dir=self.root)
        )
        try:
            for name, content in files.items():
                (staging / name).write_text(content, encoding="utf-8")
            os.replace(staging, target)
        except OSError as exc:
            raise ArtifactStoreError(
                f'Could not write Run artifacts for "{bundle.manifest.run_id}": {exc}'
            ) from exc
        finally:
            if staging.exists():
                shutil.rmtree(staging)
        return target

    def read(self, run_id: str) -> RunBundle:
        """Load and cross-check one complete bundle."""
        if not self._valid_run_id(run_id):
            raise ArtifactStoreError(f'Invalid Run ID "{run_id}"')
        directory = self.root / run_id
        try:
            manifest = RunManifest.model_validate_json(
                (directory / "manifest.json").read_text(encoding="utf-8")
            )
            scenarios = tuple(
                Scenario.model_validate_json(line)
                for line in self._read_jsonl(directory / "scenarios.jsonl")
            )
            trajectories = tuple(
                Trajectory.model_validate_json(line)
                for line in self._read_jsonl(directory / "trajectories.jsonl")
            )
        except (OSError, UnicodeError, ValidationError, ValueError) as exc:
            raise ArtifactStoreError(f'Could not read Run bundle "{run_id}": {exc}') from exc
        bundle = RunBundle(manifest, scenarios, trajectories)
        self._validate_bundle(bundle)
        if manifest.run_id != run_id:
            raise ArtifactStoreError("Run directory and manifest IDs do not match")
        return bundle

    def write_evaluations(self, bundle: EvaluationBundle) -> Path:
        """Atomically attach immutable evaluation evidence to an existing Run."""
        run = self.read(bundle.run_id)
        self._validate_evaluations(run, bundle)
        content = self._jsonl(bundle.vectors)
        target = self.root / bundle.run_id / "evaluations.jsonl"
        if target.exists():
            try:
                existing = target.read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                raise ArtifactStoreError(
                    f'Could not read existing evaluations for "{bundle.run_id}": {exc}'
                ) from exc
            if existing != content:
                raise ArtifactStoreError(
                    f'Evaluation collision: Run "{bundle.run_id}" already has '
                    "different evidence"
                )
            return target

        descriptor, temporary_name = tempfile.mkstemp(
            prefix=".evaluations.", suffix=".jsonl", dir=target.parent
        )
        os.close(descriptor)
        temporary = Path(temporary_name)
        try:
            temporary.write_text(content, encoding="utf-8")
            try:
                os.link(temporary, target)
            except FileExistsError:
                existing = target.read_text(encoding="utf-8")
                if existing != content:
                    raise ArtifactStoreError(
                        f'Evaluation collision: Run "{bundle.run_id}" already has '
                        "different evidence"
                    )
        except OSError as exc:
            raise ArtifactStoreError(
                f'Could not attach evaluations to "{bundle.run_id}": {exc}'
            ) from exc
        finally:
            temporary.unlink(missing_ok=True)
        return target

    def read_evaluations(self, run_id: str) -> EvaluationBundle:
        """Load and cross-check the Evaluation Vectors attached to a Run."""
        run = self.read(run_id)
        try:
            vectors = tuple(
                EvaluationVector.model_validate_json(line)
                for line in self._read_jsonl(self.root / run_id / "evaluations.jsonl")
            )
        except (OSError, UnicodeError, ValidationError, ValueError) as exc:
            raise ArtifactStoreError(
                f'Could not read evaluations for "{run_id}": {exc}'
            ) from exc
        evaluators = tuple(result.evaluator for result in vectors[0].results)
        bundle = EvaluationBundle(
            run_id=run_id,
            evaluators=evaluators,
            vectors=vectors,
        )
        self._validate_evaluations(run, bundle)
        return bundle

    @staticmethod
    def _jsonl(records: tuple[BaseModel, ...]) -> str:
        return "".join(record.model_dump_json() + "\n" for record in records)

    @staticmethod
    def _read_jsonl(path: Path) -> tuple[str, ...]:
        lines = tuple(line for line in path.read_text(encoding="utf-8").splitlines() if line)
        if not lines:
            raise ArtifactStoreError(f'JSONL artifact "{path.name}" is empty')
        return lines

    @staticmethod
    def _valid_run_id(run_id: str) -> bool:
        return (
            len(run_id) == 20
            and run_id.startswith("run_")
            and all(character in "0123456789abcdef" for character in run_id[4:])
        )

    @staticmethod
    def _validate_bundle(bundle: RunBundle) -> None:
        manifest = bundle.manifest
        scenario_ids = tuple(scenario.id for scenario in bundle.scenarios)
        trajectory_scenario_ids = tuple(
            trajectory.scenario_id for trajectory in bundle.trajectories
        )
        if scenario_ids != manifest.scenario_ids:
            raise ArtifactStoreError("Scenario records do not match manifest order")
        if trajectory_scenario_ids != manifest.scenario_ids:
            raise ArtifactStoreError("Trajectory records do not match manifest order")
        if any(scenario.partition != manifest.partition for scenario in bundle.scenarios):
            raise ArtifactStoreError("Scenario record does not match manifest partition")
        expected_run_id = run_id_for(
            environment_id=manifest.environment_id,
            environment_version=manifest.environment_version,
            partition=manifest.partition,
            sampling_seed=manifest.sampling_seed,
            scenarios=bundle.scenarios,
            policy=manifest.policy,
            trajectories=bundle.trajectories,
        )
        if manifest.run_id != expected_run_id:
            raise ArtifactStoreError("Run ID does not match fixed execution inputs")
        for trajectory in bundle.trajectories:
            if (
                trajectory.environment_id != manifest.environment_id
                or trajectory.environment_version != manifest.environment_version
                or trajectory.policy != manifest.policy
            ):
                raise ArtifactStoreError(
                    "Trajectory environment or Policy does not match manifest"
                )

    @staticmethod
    def _validate_evaluations(run: RunBundle, bundle: EvaluationBundle) -> None:
        if bundle.run_id != run.manifest.run_id:
            raise ArtifactStoreError("Evaluation and Run IDs do not match")
        expected_trajectory_ids = tuple(
            trajectory.trajectory_id for trajectory in run.trajectories
        )
        expected_scenario_ids = tuple(scenario.id for scenario in run.scenarios)
        actual_trajectory_ids = tuple(vector.trajectory_id for vector in bundle.vectors)
        actual_scenario_ids = tuple(vector.scenario_id for vector in bundle.vectors)
        if actual_trajectory_ids != expected_trajectory_ids:
            raise ArtifactStoreError("Evaluation Vectors do not match Trajectory order")
        if actual_scenario_ids != expected_scenario_ids:
            raise ArtifactStoreError("Evaluation Vectors do not match Scenario order")
        expected_evaluators = bundle.evaluators
        if not expected_evaluators or any(
            tuple(result.evaluator for result in vector.results) != expected_evaluators
            for vector in bundle.vectors
        ):
            raise ArtifactStoreError("Evaluation Vectors do not use one fixed ordered suite")

    @staticmethod
    def _assert_existing_matches(target: Path, expected: dict[str, str]) -> None:
        for name, content in expected.items():
            try:
                actual = (target / name).read_text(encoding="utf-8")
            except (OSError, UnicodeError) as exc:
                raise ArtifactStoreError(
                    f'Existing Run bundle "{target.name}" is incomplete: {exc}'
                ) from exc
            if actual != content:
                raise ArtifactStoreError(
                    f'Run ID collision: existing bundle "{target.name}" differs'
                )
