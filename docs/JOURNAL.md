# PeaRL Journal

Milestone and decision log. New entries go at the top.

---

## 2026-09-11 — Day 6: Decomposed Evaluation Vectors

### Shipped

- Added immutable `EvaluatorReference`, `EvaluationResult`, `EvaluationVector`,
  `EvaluationBundle`, and optional `Reward` records. Scores are finite and
  normalized; evidence mappings are recursively immutable.
- Added the canonical runtime-checkable `Evaluator` protocol, a generic
  deterministic Evaluator wrapper, and Run/Episode evaluation orchestration
  that rejects incorrectly attributed results.
- Added all six standardized E01 dimensions: task success, grounding, tool use,
  constraint compliance, escalation quality, and efficiency. The Environment
  owns their deterministic semantics; core remains environment-neutral.
- Added optional Reward aggregation requiring explicit complete weights that
  sum to one. No default scalar is produced.
- Added a structural legacy Gnomon Judge adapter with an explicit Scenario case
  factory and no dependency from PeaRL core to the Gnomon package.
- Added atomic, idempotent `evaluations.jsonl` sidecars. Evaluation never
  rewrites Run manifests, Scenarios, or Trajectories, and conflicting evidence
  is never overwritten.
- Added `pearl evaluate <run_id>` and declared the complete E01 Evaluator suite
  in its EnvironmentSpec.

### Verification

- 159/159 tests passed on Python 3.12. Day 6 tests cover all six dimensions,
  result attribution, fixed suite ordering, deep immutability, explicit Reward
  safeguards, the legacy Judge contract, atomic sidecar round-trips, collision
  refusal, source-Trajectory preservation, and the CLI exit gate.
- One complete Day 5 Run produced 32 ordered six-result Evaluation Vectors.
  Grounding, tool use, constraint compliance, and efficiency passed 32/32;
  task success and escalation quality passed 29/32.
- Ruff passed.
- Strict mypy passed across 39 source files.
- Built and installed a non-editable wheel, then reproduced the complete
  `run -> evaluate -> reload` path from `/tmp` using only packaged code and
  data: 32 Trajectories, 32 Evaluation Vectors, and 192 decomposed results.

### Deviations and concerns

- No PRD deviation.
- Three compound Search Scenarios combine missing evidence with unavailable
  authority. Their last-written task label expects `request_more_evidence`,
  while E01's non-compensatory safety constraint requires escalation. The
  vector deliberately preserves both facts: task success and escalation
  quality fail while grounding and constraint compliance pass.
- That disagreement is not hidden with a Reward. Ground Truth precedence for
  compound mutations must be made explicit before E01 reaches Gold or any
  Confirmation evidence is interpreted; it does not block Day 7's statistical
  integration over clearly named dimensions.
- No LLM Evaluator was added. The PRD's deterministic-first hierarchy and
  legacy Judge adapter satisfy Day 6 without introducing provider coupling.

### Next

Day 7 only: paired metric comparison, hard-gate regression, judge calibration,
power-aware decisions, and Gnomon Verdicts.

---

## 2026-09-08 — Day 5: Immutable trajectories and reproducible Runs

### Shipped

- Added strict `Step`, `Trajectory`, `PolicyReference`, and `RunManifest`
  records. Execution snapshots are recursively immutable and finite-JSON-only;
  traces enforce contiguous indexes and state continuity.
- Added content-derived Trajectory and Run IDs. A Run identity covers the full
  ordered Scenario records, Environment version, partition, sampling seed,
  Policy version/configuration hash, and resulting Trajectories, so stochastic
  reruns can remain distinct.
- Added the reusable async `EpisodeRunner` and ordered `BatchRunner`, with a
  fresh `EnvironmentRuntime` per Scenario and Ground Truth excluded from Policy
  context.
- Added canonical tool-call and tool-result evidence to runtime transitions and
  E01's deterministic claims and policy retrieval steps.
- Added an atomic file-first artifact store. Each Run contains
  `manifest.json`, `scenarios.jsonl`, and `trajectories.jsonl`; exact reruns are
  idempotent and conflicting content is never overwritten.
- Promoted the Day 4 E01 rules into the versioned deterministic `baseline`
  Policy and added the required `pearl run` command.

### Verification

- 147/147 tests passed on Python 3.12. Tests cover deep immutability, JSON
  validity, trace continuity, deterministic identities, Policy timing,
  partition isolation, batch ordering, bundle round-trips, idempotent writes,
  collision refusal, and runtime/manifest cross-checks.
- The exact exit gate passed: `pearl run E01 --policy baseline --partition
  search` produced Run `run_e2d9b96cae039fe3` with 32 ordered Search Scenarios
  and 32 complete Trajectories from the canonical 50-case seed-42 pool.
- Ruff passed.
- Strict mypy passed across 31 source files.
- Built a non-editable wheel, installed it into the isolated Python 3.12
  environment, and reproduced and reloaded the complete E01 Run from `/tmp`
  using only packaged code and packaged Environment data.

### Deviations and concerns

- No PRD deviation.
- The deterministic runner records zero latency by default so repeated local
  execution stays byte-stable; callers can inject a monotonic nanosecond clock
  when measured latency is part of the evidence.
- Batch execution is intentionally ordered and sequential. Concurrency remains
  outside the Day 5 contract and should be added only with explicit ordering,
  rate-limit, and failure semantics.
- Evaluation, failure, summary, and report artifacts are intentionally absent.
  They begin in their named milestones rather than appearing as empty Day 5
  files.
- No architecture or correctness concern blocks Day 6.

### Next

Day 6 only: Evaluator protocol, deterministic Evaluators, task success,
constraint compliance, and Evaluation Vectors stored separately from immutable
Trajectories.

---

## 2026-09-07 — Day 4: Runtime and Policy boundaries

### Shipped

- Added the runtime `Action`, `Observation`, `RuntimeContext`,
  `StateTransition`, and `StepResult` values separately from their declarative
  specification records.
- Added the runtime-checkable `EnvironmentRuntime` protocol and an injected
  `FunctionalEnvironmentRuntime` that owns reset, observation, stepping, state
  validation, action availability, maximum-step termination, and lifecycle
  guards without embedding E01 logic in core.
- Made reset and step updates atomic and defensive. Callback state and context
  are copied, observations must faithfully match their declared state
  projections, and invalid outputs do not partially advance runtime state.
- Added environment-version checks when a generated Scenario enters a runtime.
- Added the canonical async `Policy` protocol, deterministic `RulePolicy`, sync
  or async `CallablePolicy`, and `LegacyGnomonAgentPolicy` for Gnomon's
  `Agent.run(input: str) -> str` contract.
- Kept Scenario Ground Truth out of `RuntimeContext` and `PolicyContext`.
- Added a declarative E01 `EnvironmentSpec` and deterministic three-step Claims
  Dispute runtime covering claim inspection, both tool-availability conditions,
  policy retrieval, resolution, escalation, and declared termination.

### Verification

- 133/133 tests passed on Python 3.12. Day 4 tests cover lifecycle misuse,
  defensive snapshots, environment-version ownership, state and observation
  contract violations, unavailable actions, action arguments, both tool
  outages, maximum-step termination, all Policy adapters, and deterministic
  multi-step execution.
- The exact Day 4 exit condition passes: one sampled E01 Scenario executes as a
  complete three-step Episode. All 50 Scenarios from the Day 3 exit-gate sample
  also execute to termination through the same runtime and Policy interfaces.
- Ruff passed.
- Strict mypy passed across 27 source files.
- Built and installed the wheel into an isolated target outside the repository;
  all 23 Day 4 Runtime, Policy, and E01 Episode tests passed against the
  installed package and packaged E01 data.

### Deviations and concerns

- No PRD deviation.
- The Day 4 Episode is intentionally driven by an integration-test loop. The
  reusable Episode runner, immutable Trajectory, Step records, RunManifest, and
  JSONL artifacts remain locked to Day 5.
- `LegacyGnomonAgentPolicy` requires an explicit output parser because a legacy
  text response cannot be safely interpreted as an environment Action without
  environment-specific semantics.
- E01 is a deterministic runtime fixture, not yet the polished Gold Environment
  reserved for Day 10. Its evaluator plan is declarative only.
- Generic JSON Schema execution for Action arguments was not added. E01 checks
  its semantic action contract inside its transition function; a shared
  validator should be considered only when multiple runtimes demonstrate the
  need.
- No architecture or correctness concern blocks Day 5.

### Next

Day 5 only: immutable `Trajectory` and `Step`, `RunManifest`, JSONL artifact
store, reusable Episode runner, and batch runner.

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
