# PeaRL Journal

Milestone and decision log. New entries go at the top.

---

## 2026-09-03 — Day 2: Canonical ontology and EnvironmentSpec

### Shipped

- Added strict, immutable Pydantic v2 models for `EnvironmentSpec`, `Scenario`,
  `Action`, `Observation`, `State`, `ToolSpec`, `Constraint`, and
  `EvaluationSpec` plus their required nested records.
- Kept `EnvironmentSpec` declarative; no executable `EnvironmentRuntime` or
  Scenario generation behavior was introduced.
- Added cross-reference validation for duplicate IDs, observation/state links,
  action/tool and action/observation links, constraint/action links,
  evaluator/dimension links, Hard Gate metrics, Ground Truth state fields and
  types, maximum steps, and Scenario environment/state/tool ownership.
- Added YAML file and environment-directory loaders with concise actionable
  errors.
- Added `pearl validate`.
- Added the complete 25-entry Enterprise-25 Registry with all 25 unique
  vertical/workflow cells and required objectives, capability stresses, and
  expected failure families.
- Added `pearl registry list`.
- Packaged the canonical Registry as shared wheel data while retaining
  `environments/enterprise25/registry.yaml` as its single source.

### Verification

- 93/93 tests passed on Python 3.12, including 39 new schema, loader,
  cross-reference, Registry, and CLI tests.
- Ruff passed.
- Strict mypy passed across 11 source files.
- Built a wheel and verified from `/tmp`, outside the repository, that
  `pearl registry list` loads the packaged Registry and returns exactly 25.
- The Day 1 Gnomon statistical tests remain green.

### Deviations and concerns

- No PRD deviation.
- `vertical` and `workflow_archetype` remain extensible slugs in generic
  `EnvironmentSpec`; only `Enterprise25Registry` restricts them to the canonical
  5×5 vocabulary. This prevents the reference suite from constraining user
  environments.
- Termination condition strings are intentionally declarative in Day 2. Their
  execution semantics belong to Day 4.
- No architecture or correctness concern blocks Day 3.

### Next

Day 3 only: Seed Scenario schema, Scenario Mutator protocol, deterministic
sampling and provenance, partition labels, four generic perturbations, and the
first E01 Seed Scenarios.

---

## 2026-09-03 — Day 1 published

- Connected the local `main` branch to
  `https://github.com/subramanyanashwath/PeaRL`.
- Published the Day 1 root commit `76e0445`.
- GitHub Actions run 1 passed on the Python 3.11/3.12 matrix.
- Published Gnomon ADR-0004 in commit `6c9d07d`.
- The repository-level `AGENTS.md` now requires this journal to be updated for
  every substantive implementation session.

No product behavior or milestone scope changed during publication.

---

## 2026-09-03 — Day 1: Gnomon joins PeaRL

Day 0 repository ingestion and Day 1 migration are complete.

### Shipped

- Created the standalone PeaRL Python repository with a `src/` package layout,
  Hatchling build, MIT license, scope lock, backlog, architecture document, and
  Python 3.11/3.12 CI.
- Added the `pearl` CLI entry point with `--help` and `--version`.
- Migrated Gnomon's bootstrap and independent-proportion power modules into
  `pearl.gnomon` without changing their implementation or frozen result
  dataclasses.
- Migrated all 50 statistical reference tests and added four PeaRL package/API
  smoke tests.
- Preserved migration provenance in `NOTICE`.
- Added Gnomon ADR-0004 documenting the product relationship, compatibility
  boundaries, and decision not to archive or redirect Gnomon prematurely.
- Recorded legacy Gnomon Agent, runner, judge, result, and storage assets for
  later adapters rather than importing them into PeaRL core.

### Verification

- PeaRL: 54/54 tests passed on Python 3.12.
- PeaRL: Ruff clean; strict mypy clean across six source files.
- Isolated editable installation succeeded.
- `pearl --help`, `pearl --version`, and the complete public
  `from pearl.gnomon import ...` surface succeeded.
- Original Gnomon regression: 85/85 tests passed; Ruff and strict mypy clean.
- Migrated `bootstrap.py` and `power.py` are byte-for-byte identical to their
  Gnomon sources.

### Deviations and decisions

- No product-scope deviation.
- The distribution is named `pearl-agent` because the `pearl` PyPI distribution
  is occupied by an unrelated project. Product name, import namespace, and CLI
  remain PeaRL / `pearl`.
- Added a minimal README and `NOTICE` beyond the literal Day 1 checklist because
  package metadata requires a readme and the PRD requires attribution.

### Open concerns

- A GitHub remote must be connected before this commit can be published.
- The final distribution name should be rechecked before the first package
  release.

### Next

Day 2 only: canonical ontology, `EnvironmentSpec`, validation, YAML loading, and
the 25-entry Enterprise-25 Registry.
