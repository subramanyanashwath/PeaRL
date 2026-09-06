# PeaRL Journal

Milestone and decision log. New entries go at the top.

---

## 2026-09-05 — Day 3: Scenario distributions

### Shipped

- Added distinct strict models for human-authored `SeedScenario` records and
  generated `Scenario` records.
- Added explicit Search, Validation, and Confirmation labels with stable
  60/20/20 hash assignment independent of sample size.
- Added a runtime-checkable `ScenarioMutator` protocol and four generic bounded
  perturbations: missing evidence, conflicting truth, tool outage, and changed
  persona.
- Made mutators non-destructive and provenance-bearing. Semantic mutations can
  update Ground Truth alongside state, and every mutation records its type,
  version, and concrete parameters.
- Added configured deterministic sampling with complete replay inputs:
  Environment version, Seed Scenario, distribution version, mutator sequence,
  and random seed.
- Added four initial hand-authored E01 Seed Scenarios and a data-driven E01
  Scenario Distribution.
- Added `pearl sample E01 --n 50 --seed 42`, emitting reproducible JSON Lines.

### Verification

- 110/110 tests passed on Python 3.12, including property-based seed
  reproducibility, prefix stability, partition coverage, mutation immutability,
  Ground Truth repair, provenance, E01 data loading, and the exact CLI exit gate.
- Ruff passed.
- Strict mypy passed across 16 source files.
- Built and installed the wheel into an isolated target outside the repository.
  The packaged `pearl sample E01 --n 50 --seed 42` emitted exactly 50 lines on
  both runs with identical SHA-256 output hashes; the packaged Registry still
  returned exactly 25 entries.

### Deviations and concerns

- No PRD deviation.
- E01 has four initial Seed Scenarios, exceeding the Bronze minimum of three but
  intentionally stopping short of the eight Seed Scenarios and six mutators
  reserved for the Day 10 Gold milestone.
- E01's full `EnvironmentSpec` does not exist yet, so the Day 3 seeds validate
  against the Seed Scenario schema and Distribution ownership rules rather than
  an E01 state schema. Day 10 must reconcile them with the executable E01 spec.
- Partition labels are established now; their access-control semantics become
  enforceable when the Hill-Climber is introduced on Day 9.
- No architecture or correctness concern blocks Day 4.

### Next

Day 4 only: `EnvironmentRuntime`, `Policy`, `PolicyConfig`, deterministic
execution, LLM wrapper, legacy Gnomon Agent adapter, and mock-Policy tests.

---

## 2026-09-04 — README narrative and visual system

### Shipped

- Replaced the minimal root README with the public PeaRL narrative: the
  prototype-to-production problem, v1 environment loop, current quickstart,
  Objective + ACTRW provenance, E01 target experiment, Enterprise-25,
  Gnomon, bounded PolicyConfig improvement, interoperability boundaries,
  current status, and explicit non-goals.
- Added three accessible SVG assets for the hero, core loop, and Enterprise-25
  matrix using one restrained visual system.
- Kept every implementation claim phase-correct. The README labels E01 as a
  target and distinguishes current Gnomon capabilities from planned v1 work.

### Verification

- 93/93 tests passed on Python 3.12.
- Ruff passed.
- Strict mypy passed across 11 source files.
- All three SVGs parsed as XML, rendered to PNG, and were visually inspected at
  1.5x output resolution.
- Pandoc rendered the README from GitHub-flavored Markdown.
- All 27 local and external README references were scanned; every local target
  exists.
- Markdownlint passed with only the intentional centered HTML and long-line
  rules disabled.

### Deviations and concerns

- No product behavior, scope, or active Day 3 implementation changed.
- The README uses small HTML blocks for centered responsive assets and badges;
  the rest remains ordinary GitHub-flavored Markdown.
- No empirical E01 result is shown before the experiment exists.

### Next

Day 3 only: Seed Scenario schema, Scenario Mutator protocol, deterministic
sampling and provenance, partition labels, four generic perturbations, and the
first E01 Seed Scenarios.

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
