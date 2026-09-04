# PeaRL + FieldOS
## Canonical Product Requirements Document
### PeaRL v1.0 · FieldOS v0.5 · Gnomon Integration

**Status:** SCOPE LOCK  
**Owner:** Ashwath  
**Date:** September 2026  
**Core engineering sprint:** 14 days  
**Total calendar runway:** 30 days  
**Target engineering budget:** 76 focused hours  
**Absolute pre-RC engineering ceiling:** 84 focused hours  
**Licensing target:** MIT  
**Primary development mode:** local-first, open source, provider-neutral  
**Intended execution environment:** fresh Codex coding session with access to the existing Gnomon repository

---

# 0. CODEX EXECUTION CONTRACT

This document is normative.

A fresh coding agent should be able to implement the project from this PRD without relying on prior conversation history.

If terminology in another section conflicts with the **Canonical Terminology** section, the Canonical Terminology section wins.

If a requested implementation idea conflicts with the **Scope Lock**, the Scope Lock wins.

If a feature is attractive but is not required by this document:

1. add it to `BACKLOG.md`;
2. do not implement it during Days 1–14;
3. continue with the active milestone.

Do not invent additional product modules.

Do not broaden the project into:

- a general productivity suite;
- a CRM;
- an agent hosting platform;
- an RL training framework;
- an observability SaaS;
- a benchmark marketplace;
- a Microsoft-specific product;
- a multi-user enterprise SaaS.

The goal is depth, coherence, correctness and demonstrable technical value.

---

# 1. TL;DR

Two public products exist.

## PeaRL

**PeaRL is an environment-centric experimentation and improvement framework for AI agents.**

It:

1. represents real workflows as executable environments;
2. defines distributions of scenarios inside those environments;
3. executes agent Policies against scenarios;
4. records multi-step Trajectories;
5. evaluates behavior across decomposed dimensions;
6. uses **Gnomon** to quantify statistical evidence and uncertainty;
7. analyzes conditional Failure Distributions;
8. hill-climbs agent/harness PolicyConfigs;
9. validates final improvements against held-out scenarios.

PeaRL is the flagship technical project.

---

## FieldOS

**FieldOS is a local-first field-learning harness.**

It structures learning from:

- people;
- conversations;
- engagements;
- repeated patterns;
- resulting impact.

Its central role is to convert messy real-world knowledge into structured inputs for PeaRL and convert PeaRL findings back into reusable field knowledge.

FieldOS is intentionally small.

---

## Gnomon

**Gnomon becomes PeaRL's statistical inference subsystem.**

Gnomon answers:

> Is the apparent improvement real enough to support a decision?

It retains its existing identity:

> **From eval numbers to ship decisions.**

Gnomon is no longer developed as a competing standalone product after migration.

---

# 2. PRODUCT RELATIONSHIP

The system should be understood as two learning loops.

```text
                     REAL WORLD

            ┌────────────┴─────────────┐
            ▼                          ▼
         PEOPLE                    ENGAGEMENTS
            │                          │
            │ tacit knowledge          │ O + ACTRW
            │ experience               │ workflow
            │ beliefs                  │ constraints
            │                          │
            └────────────┬─────────────┘
                         ▼
                    FIELD OS
                         │
                    structured
                  field knowledge
                         │
                         ▼
                .pearl.yaml export
                         │
                         ▼
               ╔══════════════════╗
               ║      PeaRL       ║
               ║                  ║
               ║ Environment      ║
               ║ Scenario Dist.   ║
               ║ Policy           ║
               ║ Trajectory       ║
               ║ Evaluation       ║
               ║ Gnomon           ║
               ║ Failures         ║
               ║ Hill-Climb       ║
               ╚════════╤═════════╝
                        │
             ┌──────────┴───────────┐
             ▼                      ▼
          PATTERNS               BETTER
                                POLICIES
             │                      │
             └──────────┬───────────┘
                        ▼
                     IMPACT
                        │
                        ▼
                   NEXT PROBLEM
```

---

# 3. CAREER / PRODUCT OBJECTIVE

This project exists to create three forms of compounding leverage.

## 3.1 Operational leverage

FieldOS should make a technical field operator materially better at:

- learning from experts;
- preparing for conversations;
- capturing tacit knowledge;
- decomposing ambiguous work;
- recognizing repeated patterns;
- turning work into reusable assets.

---

## 3.2 Technical leverage

PeaRL should demonstrate real competence in:

- agent environments;
- state machines;
- agent harnesses;
- multi-step trajectories;
- evaluation design;
- experiment design;
- statistical inference;
- uncertainty quantification;
- failure analysis;
- optimization;
- reproducible software engineering.

---

## 3.3 Public proof

The public projects should let a technically sophisticated outsider inspect the work rather than relying on résumé claims.

Desired reaction:

> "This person has actually thought deeply about how agent systems behave in environments, how to measure whether changes improve them, and how field knowledge should feed that process."

---

# 4. EXISTING ASSET: GNOMON

The implementation MUST begin by inspecting:

```text
https://github.com/subramanyanashwath/gnomon
```

The current repository is not disposable.

It already contains useful tested work.

## Current useful assets

Preserve or migrate:

```text
gnomon/stats/bootstrap.py
gnomon/stats/power.py
gnomon/eval/aggregate.py
gnomon/eval/judge.py
gnomon/eval/runner.py
gnomon/agents/
gnomon/storage/
gnomon/types.py
tests/
examples/live_run_mmlu_pro.py
```

Existing concepts include:

- `Agent`;
- `EvalCase`;
- `EvalResult`;
- `EvalRun`;
- `Judge`;
- `LLMJudge`;
- `EvalRunner`;
- `BootstrapResult`;
- `PowerResult`;
- `bootstrap_ci`;
- pass-rate power analysis;
- SQLite persistence;
- lineage/source metadata.

Do not rewrite statistically tested primitives merely to make naming uniform.

---

# 5. GNOMON MIGRATION STRATEGY

## Decision

Gnomon is absorbed into PeaRL as:

```python
pearl.gnomon
```

The Gnomon public repository remains intact during the sprint for provenance.

Do NOT delete the repository.

Do NOT rewrite its git history during Days 1–14.

That provides no product value.

---

## Day-1 migration

Create:

```text
docs/decisions/0004-gnomon-joins-pearl.md
```

in the Gnomon repository documenting:

- why PeaRL now supersedes Gnomon as the flagship project;
- that Gnomon's statistical thesis remains unchanged;
- that Gnomon becomes the statistical decision subsystem inside PeaRL;
- that the repository will remain available as historical provenance.

Copy/migrate the appropriate tested Gnomon modules into:

```text
src/pearl/gnomon/
```

Preserve copyright/license attribution.

---

## Post-release

After PeaRL v1.0 is stable:

Update Gnomon's README:

> Gnomon now lives inside PeaRL as `pearl.gnomon`.

Link to PeaRL.

Optionally archive Gnomon read-only.

Do not archive Gnomon before PeaRL is demonstrably functioning.

---

# 6. CANONICAL TERMINOLOGY

This section is normative.

Do not invent synonyms in code.

---

# 6.1 Products

## PeaRL

An environment-centric experimentation and improvement framework for AI agents.

PeaRL v1 does **not** train model weights through reinforcement learning.

"PeaRL" is a product name.

Do not require a Microsoft-specific acronym expansion.

---

## FieldOS

A local-first field-learning harness for structuring knowledge from People, Interactions, Engagements, Patterns and Impact.

FieldOS can generate draft PeaRL Environment specifications.

PeaRL must not depend on FieldOS.

---

## Gnomon

PeaRL's statistical inference and experiment-decision subsystem.

Gnomon:

- does not generate scenarios;
- does not execute environments;
- does not optimize PolicyConfigs;
- does not decide what problem the agent should solve.

It answers statistical questions about evaluation evidence.

---

# 6.2 Field discovery

## Objective — O

The business outcome an Engagement exists to produce and the criteria by which success will be recognized.

Objective is established before ACTRW decomposition.

---

## ACTRW

Five dimensions used after Objective has been established.

### A — Agency

What should the agent own?

What remains human-owned?

Where are handoffs required?

---

### C — Context

What information changes the correct behavior?

Examples:

- customer state;
- historical state;
- account state;
- organizational context;
- documents;
- permissions;
- previous interactions.

---

### T — Truth

What sources are authoritative?

What happens when sources:

- disagree;
- are stale;
- are missing;
- cannot be accessed?

---

### R — Risk

What happens if the agent is wrong?

Includes:

- failure severity;
- financial consequence;
- policy consequence;
- user harm;
- compliance;
- escalation rules.

---

### W — Workflow

What is the actual end-to-end process?

Includes:

- actors;
- states;
- actions;
- systems;
- handoffs;
- transitions;
- exceptions;
- completion conditions.

---

## O + ACTRW

The complete FieldOS engagement decomposition.

The six fields must NEVER collectively be called "ACTRW."

Canonical structure:

```yaml
objective: ...

actrw:
  agency: ...
  context: ...
  truth: ...
  risk: ...
  workflow: ...
```

---

# 6.3 PeaRL runtime ontology

## EnvironmentSpec

The declarative, serializable specification of an environment.

It describes:

- objective;
- actors;
- state schema;
- observations;
- actions;
- tools;
- constraints;
- ground truth;
- termination conditions;
- evaluation requirements.

---

## EnvironmentRuntime

Executable implementation corresponding to an EnvironmentSpec.

Conceptual protocol:

```python
class EnvironmentRuntime(Protocol):
    def reset(self, scenario: Scenario) -> Observation: ...
    def observe(self) -> Observation: ...
    def step(self, action: Action) -> StepResult: ...
    def state(self) -> State: ...
```

EnvironmentSpec is declarative.

EnvironmentRuntime executes behavior.

Do not conflate them.

---

## Scenario Distribution

The set or generation process defining possible instantiated conditions inside an Environment.

---

## Scenario

One concrete instantiated situation from an Environment.

---

## Seed Scenario

A deliberately human-authored Scenario used as:

- a trusted reference case;
- a source for perturbation;
- a Gold Environment fixture.

---

## Scenario Mutator

A bounded transformation applied to a Scenario.

Examples:

- missing evidence;
- conflicting evidence;
- stale data;
- revoked permission;
- tool outage;
- ambiguous intent;
- adversarial request;
- changed persona;
- partial tool result.

Every mutation records provenance.

---

## Policy

The complete agent system being evaluated.

A Policy may contain:

- model;
- system prompt;
- instructions;
- retrieval settings;
- tools;
- tool descriptions;
- tool availability;
- orchestration;
- context formatting;
- escalation rules;
- deterministic logic.

Policy does NOT imply a learned neural-network policy.

---

## PolicyConfig

The tunable configuration of a Policy.

---

## Candidate

A proposed PolicyConfig being compared to a baseline/incumbent.

---

## Episode

One execution of one Policy against one Scenario.

---

## Trajectory

The immutable execution trace produced by an Episode.

Conceptually:

```text
s0
 ↓
o0
 ↓
a0
 ↓
tool_call
 ↓
tool_result
 ↓
s1
 ↓
o1
 ↓
a1
 ...
```

---

## Run

A batch of Episodes with fixed:

- Environment version;
- Scenario IDs;
- Policy;
- PolicyConfig;
- Evaluator versions.

---

## Replay

Executing another Policy or PolicyConfig against the same Scenario IDs/seeds.

Replay enables paired comparison.

---

## Experiment

One or more Runs intended to answer a stated hypothesis.

---

# 6.4 Evaluation ontology

## Evaluator

A versioned function mapping a Trajectory plus optional Ground Truth to one or more EvaluationResults.

---

## EvaluationResult

One structured measurement.

Example:

```json
{
  "dimension": "tool_use",
  "score": 1.0,
  "passed": true,
  "evidence": {...}
}
```

---

## Evaluation Vector

The decomposed set of measurements for an Episode or Run.

Canonical initial dimensions:

1. task success;
2. grounding;
3. tool use;
4. constraint compliance;
5. escalation quality;
6. efficiency.

---

## Reward

An OPTIONAL scalar aggregation of dimensions.

Reward must never replace the decomposed Evaluation Vector.

---

## Hard Gate

A non-compensatory requirement.

A Hard Gate cannot be offset by performance gains elsewhere.

Example:

```text
task success: +12pp
compliance:   -5pp

Hard Gate requires compliance >= baseline - 0.5pp.

Verdict: BLOCK.
```

---

## Failure

A categorized undesirable behavioral event supported by evidence.

---

## Failure Distribution

The empirical distribution of Failures across a Run.

It can be conditioned on scenario/state attributes.

Example:

```text
P(wrong_tool) = 0.18

P(wrong_tool | conflicting_truth) = 0.41
```

Conditional failure analysis is a signature PeaRL capability.

---

# 6.5 Gnomon ontology

## Bootstrap Confidence Interval

An uncertainty interval generated through bootstrap resampling.

Existing Gnomon implementation should be reused.

---

## Power Analysis

A pre-run or retrospective assessment of whether sample size is sufficient to detect a specified effect.

Existing Gnomon independent-proportion functions remain valid for their documented designs.

IMPORTANT:

Do not incorrectly apply an independent-two-proportion power function to paired replay data.

Methods must match design.

---

## Judge Calibration

Measurement of how reliably an automated Judge agrees with trusted human/reference labels.

v1 target metrics:

- Cohen's κ;
- Krippendorff's α;
- Spearman correlation for ordinal/continuous scores;
- bucketed agreement;
- optional bootstrapped uncertainty.

---

## Paired Comparison

A comparison where baseline and candidate Policies run on the same Scenario IDs.

Paired comparison is PeaRL's default experiment design.

---

## Regression

A measurable deterioration in an evaluation dimension relative to baseline.

---

## Verdict

Canonical v1 verdicts:

### SHIP

Evidence supports adopting the Candidate and all Hard Gates pass.

### ITERATE

Candidate does not yet meet adoption criteria but no catastrophic Hard Gate invalidates further search.

### BLOCK

Candidate violates a Hard Gate or shows an unacceptable material regression.

### UNDERPOWERED

The experiment lacks adequate sample size for the minimum effect size the user claims to care about.

### INVALID

The experiment cannot support inference because of broken/misaligned data, evaluator failure, scenario corruption or experiment-design violation.

Do not use "INCONCLUSIVE" as a catch-all.

Use a specific reason.

---

# 6.6 Optimization ontology

## Hill-Climbing

A bounded local PolicyConfig search procedure.

PeaRL v1:

1. proposes neighboring Candidate configs;
2. evaluates them on a search partition;
3. selects candidates on a validation partition;
4. performs final Gnomon confirmation on held-out scenarios;
5. retains an acceptable candidate;
6. repeats until stopping condition.

Hill-Climbing is NOT RL training.

---

# 6.7 FieldOS ontology

## Person

A human knowledge source.

---

## Interaction

One substantive conversation or working interaction involving one or more People.

---

## Engagement

A field problem represented using Objective + ACTRW plus supporting metadata.

---

## Pattern

A human-reviewable hypothesis about a recurring phenomenon supported by multiple evidence sources.

Possible evidence:

- Interactions;
- Engagements;
- PeaRL Runs;
- Failures;
- other artifacts.

---

## Impact

A structured record connecting:

- problem;
- contribution;
- artifact;
- outcome;
- metric/evidence;
- collaborators;
- date.

---

# 6.8 Environment maturity

## Registry Environment

A named environment slot with:

- ID;
- vertical;
- workflow archetype;
- objective;
- primary capability stresses;
- expected failure families.

No executable runtime required.

---

## Bronze Environment

Schema-complete environment.

Requirements:

- valid EnvironmentSpec;
- Objective + ACTRW provenance;
- state model;
- actions;
- tools;
- constraints;
- ground truth;
- evaluator plan;
- >=3 Seed Scenarios.

End-to-end optimization is not required.

---

## Gold Environment

Reference-quality executable environment.

Requirements:

- everything required for Bronze;
- realistic state transitions;
- >=8 hand-designed Seed Scenarios;
- >=4 perturbation families;
- >=50 reproducible generated Scenarios;
- baseline Policy;
- meaningfully improved Candidate Policy;
- full Trajectory capture;
- >=4 evaluation dimensions;
- known intentional failure regime;
- Failure Distribution;
- paired Replay;
- Gnomon comparison;
- successful Hill-Climb;
- automated tests;
- documentation.

Gold must mean something.

---

# 7. THE PeaRL ENTERPRISE-25 SUITE

PeaRL includes a canonical 5×5 suite.

## Verticals

1. FSI / Insurance
2. Healthcare
3. Retail
4. Manufacturing
5. Transportation / Logistics

## Workflow archetypes

1. Support / Resolution
2. Research / Investigation
3. Compliance / Review
4. Operations / Exceptions
5. Planning / Decision

---

# 7.1 Canonical matrix

| ID | FSI / Insurance | Healthcare | Retail | Manufacturing | Transportation |
|---|---|---|---|---|---|
| Support / Resolution | **E01 Claims Dispute Resolution** | **E02 Prior Authorization Appeal** | **E03 Store Escalation Resolution** | **E04 Supplier Quality Dispute** | **E05 Delivery Exception Resolution** |
| Research / Investigation | **E06 Credit Deterioration Investigation** | **E07 Utilization Anomaly Investigation** | **E08 Merchandising Performance Investigation** | **E09 Quality Root-Cause Investigation** | **E10 Network Delay Root-Cause Investigation** |
| Compliance / Review | **E11 KYC / AML Case Review** | **E12 Medical-Necessity Compliance Review** | **E13 Pricing & Promotion Compliance Audit** | **E14 Supplier Regulatory Documentation Review** | **E15 Customs & Shipping Documentation Review** |
| Operations / Exceptions | **E16 Account Servicing Exception** | **E17 Claims Adjudication Exception** | **E18 Inventory Replenishment Exception** | **E19 Production Disruption Recovery** | **E20 Shipment Routing Exception** |
| Planning / Decision | **E21 Credit Workout Planning** | **E22 Care Coordination Planning** | **E23 Assortment & Inventory Planning** | **E24 Production Capacity Planning** | **E25 Network Capacity & Route Planning** |

---

# 7.2 v1 Gold diagonal

Five Gold Environments MUST ship.

They deliberately span all five verticals and all five workflow archetypes.

## G1 — E01
Claims Dispute Resolution

**Vertical:** FSI / Insurance  
**Workflow:** Support / Resolution

Primary stresses:

- conflicting truth;
- evidence completeness;
- grounding;
- tool routing;
- escalation;
- human approval.

This is the flagship environment.

---

## G2 — E07
Utilization Anomaly Investigation

**Vertical:** Healthcare  
**Workflow:** Research / Investigation

Primary stresses:

- multi-source evidence;
- anomaly interpretation;
- investigation sequencing;
- false correlations;
- incomplete context;
- human interpretation.

---

## G3 — E13
Pricing & Promotion Compliance Audit

**Vertical:** Retail  
**Workflow:** Compliance / Review

Primary stresses:

- policy/rule compliance;
- temporal conditions;
- conflicting commercial rules;
- exception handling;
- documentation;
- hard gates.

---

## G4 — E19
Production Disruption Recovery

**Vertical:** Manufacturing  
**Workflow:** Operations / Exceptions

Primary stresses:

- dynamic state;
- sequencing;
- tool/system outages;
- operational dependencies;
- recovery actions;
- human handoffs.

---

## G5 — E25
Network Capacity & Route Planning

**Vertical:** Transportation / Logistics  
**Workflow:** Planning / Decision

Primary stresses:

- tradeoffs;
- multi-step planning;
- changing constraints;
- resource allocation;
- delayed consequences;
- efficiency.

---

# 7.3 Environment goals

## Day 14

Required:

```text
25 / 25 Registry
5 / 25 Gold
```

## Day 30

Target:

```text
25 / 25 Registry
5 / 25 Gold
20 / 25 Bronze
```

Do not create 25 Gold Environments during this project phase.

That is a content-generation trap.

---

# 8. CORE PeaRL ARCHITECTURE

Recommended repository:

```text
pearl/
├── pyproject.toml
├── README.md
├── LICENSE
├── SCOPE.md
├── BACKLOG.md
├── ARCHITECTURE.md
├── CHANGELOG.md
│
├── src/
│   └── pearl/
│       ├── __init__.py
│       │
│       ├── spec/
│       │   ├── environment.py
│       │   ├── scenario.py
│       │   ├── policy.py
│       │   ├── trajectory.py
│       │   ├── evaluation.py
│       │   ├── failure.py
│       │   └── experiment.py
│       │
│       ├── runtime/
│       │   ├── environment.py
│       │   ├── episode.py
│       │   ├── runner.py
│       │   └── artifacts.py
│       │
│       ├── scenarios/
│       │   ├── sampling.py
│       │   ├── mutators.py
│       │   └── partitions.py
│       │
│       ├── policies/
│       │   ├── base.py
│       │   ├── rule.py
│       │   └── adapters.py
│       │
│       ├── evaluators/
│       │   ├── base.py
│       │   ├── deterministic.py
│       │   └── judge.py
│       │
│       ├── gnomon/
│       │   ├── bootstrap.py
│       │   ├── power.py
│       │   ├── calibration.py
│       │   ├── compare.py
│       │   ├── verdict.py
│       │   ├── report.py
│       │   └── compat.py
│       │
│       ├── failures/
│       │   ├── taxonomy.py
│       │   ├── classify.py
│       │   └── distribution.py
│       │
│       ├── optimize/
│       │   ├── mutation.py
│       │   ├── candidate.py
│       │   └── hillclimb.py
│       │
│       ├── adapters/
│       │   ├── legacy_gnomon.py
│       │   └── anthropic.py
│       │
│       └── cli/
│           └── app.py
│
├── environments/
│   └── enterprise25/
│       ├── registry.yaml
│       ├── E01_claims_dispute/
│       ├── E07_utilization_anomaly/
│       ├── E13_pricing_compliance/
│       ├── E19_production_disruption/
│       └── E25_network_planning/
│
├── examples/
├── tests/
└── docs/
    ├── concepts/
    ├── methodology/
    ├── decisions/
    └── reports/
```

---

# 9. MODELING DECISIONS

## 9.1 Pydantic versus dataclasses

New serializable PeaRL domain entities SHOULD use Pydantic v2.

Examples:

- EnvironmentSpec;
- Scenario;
- Trajectory;
- EvaluationResult;
- Failure;
- RunManifest;
- ExperimentSpec.

However:

Do NOT rewrite stable Gnomon statistical result dataclasses solely for stylistic consistency.

Existing tested objects such as:

- `BootstrapResult`;
- `PowerResult`;

may remain frozen dataclasses.

Correctness > aesthetic uniformity.

---

# 9.2 Existing Gnomon types

Current:

```text
EvalCase
EvalResult
EvalRun
Agent
Judge
```

become legacy compatibility concepts.

Mapping:

```text
Gnomon EvalCase
        ↓
PeaRL Scenario / single-turn adapter

Gnomon EvalResult
        ↓
one-step Trajectory + EvaluationResult

Gnomon EvalRun
        ↓
PeaRL Run

Gnomon Agent
        ↓
Policy adapter

Gnomon Judge
        ↓
Evaluator adapter
```

Do not make PeaRL core depend on legacy Gnomon types.

---

# 10. EnvironmentSpec

Required high-level schema:

```yaml
pearl_spec_version: "1.0"

metadata:
  id: enterprise25.E01
  name: Claims Dispute Resolution
  version: 1
  vertical: fsi_insurance
  workflow_archetype: support_resolution
  tags: []

objective:
  task: resolve_claim_dispute
  business_goal: >
    Produce an accurate, policy-grounded recommendation
    while escalating cases requiring human judgment.

actors: []

state_schema: {}

observations: []

actions: []

tools: []

constraints: []

ground_truth: []

termination:
  max_steps: 12
  success_conditions: []
  failure_conditions: []

evaluation:
  dimensions: []
  hard_gates: []

provenance:
  objective: {}
  actrw:
    agency: {}
    context: {}
    truth: {}
    risk: {}
    workflow: {}
```

---

# 10.1 Validation requirements

`pearl validate` MUST detect:

- missing required fields;
- invalid schema version;
- duplicate IDs;
- invalid action references;
- tool references to nonexistent tools;
- evaluator references to nonexistent dimensions;
- invalid hard-gate metric names;
- impossible max-step values;
- malformed Ground Truth configuration;
- invalid State defaults;
- broken Scenario references.

Errors must be actionable.

Bad:

```text
ValidationError at path foo.bar
```

Good:

```text
Environment enterprise25.E01 references tool
"policy_search" in action "retrieve_policy", but no tool
with id "policy_search" is defined.
```

---

# 11. Scenario system

Scenario example:

```yaml
id: E01.S0142

environment_id: enterprise25.E01
seed: 142

initial_state:
  claim_status: open
  evidence_complete: false

persona:
  type: frustrated_claimant

conditions:
  - conflicting_truth
  - missing_evidence

tool_conditions:
  policy_store: healthy
  claims_api: healthy

ground_truth:
  expected_resolution: request_more_evidence

provenance:
  seed_scenario: E01.seed.04
  mutations:
    - missing_evidence
    - conflicting_truth
```

---

# 11.1 Reproducibility

Same:

```text
Environment version
Seed Scenario
Mutator sequence
random seed
```

must produce the same Scenario.

---

# 11.2 Partitioning

Gold environments must define:

```text
search
validation
confirmation
```

partitions.

Why:

Hill-climbing repeatedly evaluating the same cases can overfit the eval set.

Therefore:

### Search

Used for candidate generation and local hill-climbing.

### Validation

Used for candidate selection.

### Confirmation

Held out from optimization.

Gnomon's final SHIP decision must use confirmation evidence.

---

# 11.3 Critical statistical rule

A candidate selected because it performed best on a set must not subsequently be described as statistically confirmed using that same set without qualification.

Search is optimization.

Confirmation is inference.

PeaRL must make this distinction explicit.

This is a core quality bar.

---

# 12. Policy interface

Canonical async conceptual interface:

```python
class Policy(Protocol):
    name: str
    version: str

    async def act(
        self,
        observation: Observation,
        context: PolicyContext,
    ) -> Action:
        ...
```

Why async:

Real model/tool execution is network-bound.

However deterministic sync Policies must be trivially adaptable.

---

## v1 Policies

Must include:

### RulePolicy

Deterministic.

Used heavily in CI.

---

### CallablePolicy

Wraps user functions.

---

### LegacyAgentPolicy

Wraps current Gnomon:

```python
Agent.run(input: str) -> str
```

as a one-step PeaRL Policy.

---

### Optional structured LLM Policy

One provider implementation is sufficient for v1.

Anthropic is preferred because useful code already exists in Gnomon.

Provider integration is not the product.

---

# 13. Trajectory

Canonical shape:

```json
{
  "trajectory_id": "...",
  "environment_id": "enterprise25.E01",
  "environment_version": 1,
  "scenario_id": "E01.S0142",

  "policy": {
    "name": "claims_policy",
    "version": "0.2",
    "config_hash": "..."
  },

  "steps": [
    {
      "index": 0,
      "state_before": {},
      "observation": {},
      "action": {},
      "tool_call": null,
      "tool_result": null,
      "state_after": {},
      "latency_ms": 0
    }
  ],

  "termination_reason": "success",
  "runtime_metadata": {}
}
```

Trajectories are immutable.

Evaluation attaches separate records.

Do not mutate historical Trajectory data after scoring.

---

# 14. Run artifacts

File-based artifact bundles are the canonical PeaRL source of truth.

Example:

```text
runs/
└── run_20260905_001/
    ├── manifest.json
    ├── scenarios.jsonl
    ├── trajectories.jsonl
    ├── evaluations.jsonl
    ├── failures.jsonl
    ├── summary.json
    └── report.html
```

Why file-first:

- reproducibility;
- portability;
- inspectability;
- Git-friendly synthetic fixtures;
- easier OSS debugging.

---

## Existing Gnomon SQLite

Preserve existing SQLite code.

Do not make it the only source of truth.

It can become:

- optional run index;
- report registry;
- compatibility storage backend.

Do not burn sprint hours redesigning the database.

---

# 15. Evaluation Framework

Protocol:

```python
class Evaluator(Protocol):
    name: str
    version: str
    dimension: str

    def evaluate(
        self,
        trajectory: Trajectory,
        scenario: Scenario,
    ) -> EvaluationResult:
        ...
```

---

# 15.1 Standard dimensions

v1 standardizes:

## Task Success

Did the Policy accomplish the Scenario objective?

---

## Grounding

Was behavior supported by authoritative sources?

---

## Tool Use

Did the Policy choose and use the appropriate tools?

---

## Constraint Compliance

Were hard rules respected?

---

## Escalation Quality

Was human involvement triggered appropriately?

---

## Efficiency

Did the Policy achieve the task without unnecessary steps/calls?

---

# 15.2 Evaluation hierarchy

Prefer:

1. deterministic ground truth;
2. rules;
3. reference comparisons;
4. LLM judges.

Do not use an LLM judge merely because it sounds sophisticated.

---

# 16. GNOMON INSIDE PeaRL

Gnomon's internal package:

```text
pearl.gnomon
```

retains the conceptual identity:

> Statistical decision layer.

---

# 16.1 Existing Gnomon assets to preserve

Current tested primitives should be migrated with minimal change:

### Bootstrap

Existing:

```python
bootstrap_ci(...)
BootstrapResult
```

Preserve API semantics where practical.

---

### Power

Existing:

```python
cohens_h
required_n_one_proportion
required_n_two_proportions
power_one_proportion
power_two_proportions
PowerResult
```

Preserve.

Document designs carefully.

---

### Judge

Existing LLMJudge can become an evaluator adapter.

Do not throw away tested structured-output behavior.

---

### Aggregate CI

Existing `score_ci` can remain as compatibility utility.

PeaRL's new evaluation vectors require more general aggregation.

---

# 16.2 Gnomon new v1 requirements

## A. Paired metric comparison

Given baseline and Candidate values paired by Scenario ID:

produce:

```text
baseline estimate
candidate estimate
paired delta
CI on delta
n pairs
method
```

---

## B. Metric-aware comparison

Support at minimum:

- binary pass/fail;
- continuous bounded score.

Do not silently apply a statistical method designed for one metric type to another.

---

## C. Judge calibration

Implement:

### Cohen's κ

For categorical/binary judgments.

### Krippendorff's α

For reliability where appropriate.

### Spearman correlation

For ordinal/continuous judge scoring.

### Bucketed agreement

Example:

```text
human 0–0.2   judge 0–0.2 : 81%
human 0.2–0.4 judge 0.2–0.4: 72%
...
```

Calibration report must explicitly answer:

> Is this Judge reliable enough for the effect size being interpreted?

---

## D. Power analysis

Existing Gnomon power functions remain.

For PeaRL paired experiments:

Do not pretend existing independent-arm calculations are paired power analysis.

If no statistically justified paired-power implementation exists for a metric:

Gnomon must say so.

A world-class system is allowed to say:

```text
Power calculation unavailable for this design.
```

It is not allowed to fabricate rigor.

---

## E. Hard-gate regression

Experiment may improve target metric while violating a Hard Gate.

Return BLOCK.

---

## F. Decision report

Canonical:

```text
VERDICT: SHIP

Primary metric:
task_success +8.2pp

95% paired bootstrap CI:
[+3.0pp, +13.4pp]

Failure:
wrong_tool
18.1% → 7.3%

Grounding:
Δ -0.4pp
within permitted regression band

Compliance:
Hard Gate PASS

Scenario pairs:
n = 120

Environment:
enterprise25.E01 v1
```

---

# 16.3 Deferred Gnomon features

Do NOT implement during Days 1–14:

- Bayesian A/B;
- multi-arm bandits;
- production telemetry;
- distribution-shift monitoring;
- multi-judge ensemble systems;
- generalized sequential testing;
- alpha-spending framework;
- longitudinal experiment service;
- hosted experiment registry.

The existing Gnomon PRD previously planned sequential testing.

The integrated PeaRL v1 explicitly defers generalized sequential testing in favor of:

- pre-specified sample sizes where applicable;
- paired replay;
- held-out confirmation;
- explicit power reporting.

This is a deliberate scope and correctness decision.

---

# 17. Failure system

Canonical taxonomy:

## Grounding

- unsupported claim;
- wrong source;
- stale source;
- conflicting-source mishandling.

## Tool

- wrong tool;
- missing tool;
- malformed arguments;
- ignored result;
- unnecessary repeated call.

## State

- state loss;
- stale state;
- incorrect state update.

## Planning

- wrong action sequence;
- premature termination;
- unnecessary action;
- failure to replan.

## Human coordination

- missed escalation;
- premature escalation;
- incomplete handoff.

## Constraint

- unauthorized action;
- compliance violation;
- policy-boundary violation.

## Evaluation

- ambiguous Ground Truth;
- broken Scenario;
- evaluator disagreement;
- evaluator failure.

The evaluation category is essential.

PeaRL must distinguish:

```text
agent failure
```

from:

```text
broken eval
```

---

# 18. Failure Distribution API

Examples:

```bash
pearl failures run_001
```

Output:

```text
FAILURE DISTRIBUTION

wrong_tool                 18.2%
conflicting_truth          12.4%
premature_answer            8.1%
state_loss                  6.4%
missed_escalation           4.8%
constraint_violation        1.0%
```

---

## Conditional slicing

```bash
pearl failures run_001 --slice condition_tags
```

Output:

```text
WRONG TOOL

normal_evidence             2.8%
missing_evidence             9.4%
conflicting_truth           41.2%
```

This is a signature PeaRL capability.

---

# 19. Hill-Climbing

Entities:

```text
PolicyConfig
PolicyConfigMutation
Candidate
SearchGeneration
Experiment
Verdict
```

---

# 19.1 Algorithm

```text
baseline P0

     ↓

evaluate on SEARCH

     ↓

generate bounded neighbors:
P1 P2 P3

     ↓

compare search performance

     ↓

retain promising candidates

     ↓

VALIDATION replay

     ↓

select candidate

     ↓

held-out CONFIRMATION replay

     ↓

Gnomon

     ↓

SHIP / ITERATE / BLOCK /
UNDERPOWERED / INVALID
```

---

# 19.2 v1 optimizer

Greedy/local hill climb.

No:

- PPO;
- GRPO;
- RLHF;
- policy gradients;
- Bayesian optimization;
- evolutionary search;
- model-weight training.

---

# 19.3 Mutation targets

Examples:

- system instruction variant;
- tool description;
- tool availability;
- grounding requirement;
- escalation threshold;
- context formatting;
- evidence threshold;
- retrieval parameter;
- orchestration rule.

---

# 19.4 Mutation safety

Each mutation must:

- have a deterministic ID;
- record parent config hash;
- record changed fields;
- preserve unrelated config;
- be reversible;
- appear in report diff.

---

# 20. CLI

CLI is P0.

UI is not required for PeaRL v1.

Required commands:

```bash
pearl --help

pearl registry list

pearl validate environments/enterprise25/E01_claims_dispute

pearl sample E01 --n 100 --seed 42

pearl run E01 --policy baseline --partition search

pearl evaluate <run_id>

pearl failures <run_id>

pearl compare <baseline_run> <candidate_run>

pearl optimize E01 --policy baseline

pearl report <experiment_id>
```

---

# 21. PeaRL HTML report

Gnomon's existing HTML-first philosophy survives.

A self-contained HTML report should contain:

## Header

- Environment;
- Policies;
- Experiment;
- Verdict.

## Executive result

Primary metric delta.

CI.

Power status.

Hard Gates.

---

## Evaluation vectors

Baseline versus Candidate.

---

## Failure distribution

Absolute and conditional.

---

## Config diff

What changed?

---

## Scenario coverage

Which conditions were tested?

---

## Trajectory examples

Representative:

- success;
- failure;
- repaired failure.

---

## Statistical methodology

Methods used.

---

## Limitations

Mandatory.

No report ships without an honest limitations section.

---

# 22. PeaRL Gold Environment requirements

## E01

Flagship.

Target:

```text
>= 8 Seed Scenarios
>= 6 Mutator families
>= 150 generated Scenarios
>= 5 evaluation dimensions
>= 1 intentional baseline failure regime
>= 1 successful Candidate improvement
>= 1 complete held-out Gnomon confirmation
```

---

## E07 / E13 / E19 / E25

Target each:

```text
>= 8 Seed Scenarios
>= 4 Mutator families
>= 50 Scenarios
>= 4 evaluation dimensions
>= 1 known failure regime
>= 1 Policy improvement
>= 1 paired comparison
```

Do not give all five environments equal narrative polish.

E01 is the demo.

The other four prove generality.

---

# 23. FIELDOS PRODUCT SCOPE

FieldOS v0.5 has exactly six functional primitives.

Nothing else.

---

# F1. People Engine

Schema:

```text
Person

id
name
role
organization

expertise[]
domains[]

what_they_know[]
what_i_want_to_learn[]

key_beliefs[]
open_questions[]

what_i_can_help_with[]
artifacts_shared[]

last_interaction
next_natural_touchpoint

visibility
```

No:

- sponsor score;
- relationship score;
- networking score;
- gamification.

---

# F2. Coffee Chat / Conversation Prep

Given Person + relevant prior context:

generate one-screen prep.

Required output:

## Who

Three-line maximum.

## Expertise

What do they know unusually well?

## Prior learning

What have I already learned from them?

## Current learning objective

Exactly one.

## Knowledge gaps

What am I trying to understand?

## Best questions

2–3 only.

## Give

What useful observation/artifact/context might I contribute?

## Open loop

What previous commitment or thread should be revisited?

---

## UX target

Prep brief readable in:

```text
<= 60 seconds
```

---

# F3. Interaction Capture + Multi-Conversation Synthesis

Post-interaction form:

```text
what_i_learned
what_changed_my_model
what_they_care_about
people_or_resources_mentioned
open_loop
```

Target completion:

```text
< 2 minutes
```

---

## Synthesis

User selects N Interactions.

System produces:

```text
convergences
contradictions
new_knowledge
unresolved_questions
pattern_candidates
implications_for_work
implications_for_pearl
```

---

## AI provider rule

Structured FieldOS functionality must work without a networked LLM.

AI synthesis is an OPTIONAL provider layer.

Default:

```text
disabled
```

FieldOS must never silently send professional notes to a third-party provider.

Define:

```typescript
interface SynthesisProvider {
  synthesize(input: SynthesisInput): Promise<SynthesisOutput>
}
```

Users explicitly configure providers.

---

# F4. Engagement Engine

Schema:

```text
Engagement

id
title

objective

actrw:
    agency
    context
    truth
    risk
    workflow

stakeholders[]
related_people[]
constraints[]
open_questions[]

visibility
```

---

# F5. PeaRL Bridge

From Engagement:

```text
Export Draft PeaRL Environment
```

Generates:

```text
<engagement>.pearl.yaml
```

Must clearly include:

```yaml
status: draft
```

FieldOS MUST NOT imply that O + ACTRW automatically defines a correct executable environment.

Human review is required.

---

# F6. Pattern + Impact

## Pattern

```text
id

observation

evidence:
  interactions[]
  engagements[]
  pearl_runs[]
  failures[]

hypothesized_root_cause
confidence
reusable_asset
next_action
```

---

## Impact

```text
id
date

problem
my_contribution
artifact
outcome
metric_or_evidence
collaborators[]
```

No promotion algorithm.

No L64 classifier.

Structured evidence is enough.

---

# 24. Weekly FieldOS synthesis

Template only.

No engineering effort beyond rendering/storage if trivial.

```text
1. What moved?
2. What did I learn?
3. What surprised me?
4. What failed?
5. What repeated?
6. What became reusable?
7. What is the highest-EV move next week?
```

---

# 25. FieldOS Architecture

Recommended:

```text
fieldos/
├── README.md
├── LICENSE
├── SCOPE.md
├── BACKLOG.md
│
├── app/
│   ├── people/
│   ├── interactions/
│   ├── engagements/
│   ├── patterns/
│   └── impact/
│
├── db/
│   ├── schema.ts
│   └── migrations/
│
├── lib/
│   ├── pearl/
│   │   └── export.ts
│   ├── synthesis/
│   │   ├── provider.ts
│   │   └── deterministic.ts
│   └── privacy/
│
└── examples/
```

Stack:

- TypeScript;
- Next.js;
- SQLite;
- Drizzle;
- Zod.

No separate backend.

No Redis.

No hosted infrastructure requirement.

---

# 26. Privacy architecture

FieldOS is designed to eventually contain sensitive professional context.

Privacy is P0.

Every relevant object:

```text
visibility:
    private
    public
```

Potential future employer-specific classifications are OUT OF SCOPE.

---

## Public export

Must exclude private records by default.

Never require:

```text
--exclude-private
```

Safe behavior is default.

---

## Local files

All personal databases/data directories:

```text
.gitignore
```

by default.

Fixtures are synthetic.

---

# 27. Open-source / employer boundary

The public cores contain:

- generic code;
- synthetic examples;
- public documentation;
- synthetic enterprise environments.

They do NOT contain:

- customer transcripts;
- private company data;
- internal product information;
- confidential architecture;
- internal code;
- nonpublic employee information.

The open-source abstraction may learn conceptually from real work.

The confidential state does not enter the public repository.

---

# 28. Engineering stack

## PeaRL

Python >=3.11.

Preserve Gnomon's existing compatibility where practical.

Dependencies:

Core:

```text
pydantic
typer
rich
numpy
scipy
pyyaml
```

Dev:

```text
pytest
ruff
mypy
hypothesis
```

Optional:

```text
anthropic
```

Avoid unnecessary framework dependencies.

---

## Packaging

Use one modern package manager/build setup.

Do not spend meaningful sprint time migrating build tooling solely for fashion.

Existing Gnomon uses Hatchling.

PeaRL may retain Hatchling unless a concrete blocking reason exists.

---

# 29. Testing philosophy

PeaRL should have a higher test-to-code ratio than an ordinary side project.

---

## 29.1 Schema tests

Test:

- valid EnvironmentSpecs;
- malformed Specs;
- invalid references;
- version errors.

---

## 29.2 Scenario property tests

Invariants survive mutation.

Same seed produces same output.

---

## 29.3 Runtime tests

State transitions.

Termination.

Tool behavior.

---

## 29.4 Trajectory tests

Every transition is recorded.

No historical mutation.

---

## 29.5 Gnomon tests

Statistical correctness is non-negotiable.

Every new stats function should have one or more of:

- scipy reference;
- R reference;
- analytically known result;
- simulation property.

Preserve existing Gnomon test rigor.

---

## 29.6 Failure tests

Known synthetic behaviors produce known failure categories.

---

## 29.7 Optimizer tests

Given deliberately improvable deterministic Policies:

hill-climber must find improvement.

---

## 29.8 Gold generality test

All five Gold environments must execute through the same PeaRL core without environment-specific branching in generic modules.

Bad:

```python
if env_id == "E19":
    ...
```

in core.

Not allowed.

---

# 30. Reproducibility

Every Run manifest records:

```text
pearl version
environment ID
environment version
scenario IDs
scenario seeds
policy name
policy version
config hash
evaluator versions
gnomon method versions
timestamp
git commit if available
runtime metadata
```

---

# 31. Engineering budget

Core sprint target:

# 76 hours

Hard ceiling:

# 84 hours

---

## Allocation

| Workstream | Hours |
|---|---:|
| PeaRL/Gnomon migration + scaffolding | 6 |
| canonical schemas / environment system | 8 |
| scenario distribution / partitioning | 7 |
| Policy/runtime execution | 7 |
| Trajectory + Run artifacts | 6 |
| evaluator system | 5 |
| Gnomon completion/integration | 8 |
| Failure Distribution | 5 |
| hill-climber | 7 |
| Enterprise-25 + Gold environments | 8 |
| FieldOS People/Prep/Synthesis | 4 |
| FieldOS Engagement/Bridge/Pattern/Impact | 3 |
| release/docs/integration | 2 |
| **Total** | **76** |

---

# 32. Why Gnomon saves engineering budget

Do NOT budget time for reimplementing:

- bootstrap confidence intervals;
- independent pass-rate power analysis;
- basic LLM judge scaffolding;
- single-turn evaluation compatibility;
- existing Anthropic call plumbing;
- basic storage primitives.

Those already exist.

Saved time gets redirected to:

- Environment semantics;
- Scenario distributions;
- Trajectories;
- paired experiments;
- Failure Distributions;
- Gold environments;
- held-out optimization.

---

# 33. Scope exclusions

## PeaRL NOT v1

- model-weight RL training;
- PPO;
- GRPO;
- reward-model training;
- distributed workers;
- Kubernetes;
- cloud SaaS;
- multi-tenant service;
- production telemetry;
- complex observability;
- plugin marketplace;
- dozens of provider adapters;
- automatic environment generation from arbitrary text;
- full browser UI;
- generic Bayesian optimization;
- generative scenario agent;
- generalized sequential hypothesis-testing service.

---

## FieldOS NOT v0.5

- task manager;
- calendar;
- Gmail;
- Teams;
- Slack;
- transcript import;
- automatic meeting recording;
- CRM automation;
- notifications;
- relationship scores;
- sponsor scores;
- org-chart scraping;
- LinkedIn scraping;
- vector database;
- knowledge graph visualization;
- promotion predictor;
- mobile app;
- multi-user collaboration;
- permissions admin system.

---

# 34. Five-minute PeaRL demo

This is a release requirement.

## Minute 0–1

Show:

```text
E01 Claims Dispute Resolution
```

Explain:

> "PeaRL models the workflow as an environment rather than evaluating isolated prompts."

---

## Minute 1–2

Generate scenarios.

Show:

- complete evidence;
- missing evidence;
- conflicting evidence;
- tool outage;
- escalation case.

---

## Minute 2–3

Run baseline.

Show Failure Distribution.

Key moment:

```text
overall task success = 76%

but

wrong_tool | conflicting_truth = 44%
```

The aggregate metric hid the structural failure.

---

## Minute 3–4

Show PolicyConfig mutation.

Replay.

---

## Minute 4–5

Show Gnomon confirmation:

```text
P0 → P1

Task success       +8.4pp
Wrong-tool failure -13.2pp
Grounding          -0.2pp
Compliance          PASS

95% paired CI:
[+3.1pp, +13.6pp]

VERDICT: SHIP
```

Then:

```text
pearl optimize E01
```

---

# 35. Five-minute FieldOS demo

## Minute 0–1

Open Person.

Show accumulated beliefs/knowledge.

---

## Minute 1–2

Generate Coffee Chat Prep.

---

## Minute 2–3

Select five Interactions.

Show convergence/contradiction synthesis.

---

## Minute 3–4

Open Engagement.

Show O + ACTRW.

Export draft Environment.

---

## Minute 4–5

Show PeaRL finding returning as:

- Pattern;
- Impact.

That's enough.

---

# 36. DAY-BY-DAY CORE SPRINT

---

# DAY 1 — Gnomon → PeaRL migration

**Budget: 5h**

Ship:

- create PeaRL repo;
- MIT license;
- `SCOPE.md`;
- `BACKLOG.md`;
- `ARCHITECTURE.md`;
- CI;
- Python package;
- `pearl --help`;
- migrate Gnomon statistical source;
- migrate relevant Gnomon tests;
- all migrated tests green;
- create Gnomon ADR-0004.

No feature invention.

### Exit condition

Existing Gnomon primitives are callable through:

```python
from pearl.gnomon import ...
```

---

# DAY 2 — Canonical ontology + EnvironmentSpec

**Budget: 5h**

Ship:

- Pydantic EnvironmentSpec;
- Scenario model;
- Action;
- Observation;
- State;
- ToolSpec;
- Constraint;
- EvaluationSpec;
- YAML loader;
- validation.

Also ship:

```text
enterprise25/registry.yaml
```

containing all 25 Registry environments.

### Exit condition

```bash
pearl registry list
```

returns 25.

---

# DAY 3 — Scenario distributions

**Budget: 5h**

Ship:

- Seed Scenario schema;
- Scenario Mutator protocol;
- seeded deterministic sampling;
- provenance;
- partition labels;
- 4 generic perturbations.

E01 gets first Seed Scenarios.

### Exit condition

```bash
pearl sample E01 --n 50 --seed 42
```

is reproducible.

---

# DAY 4 — Runtime + Policy

**Budget: 5h**

Ship:

- EnvironmentRuntime;
- reset;
- observe;
- step;
- termination;
- Policy protocol;
- RulePolicy;
- CallablePolicy;
- LegacyGnomonAgentPolicy.

### Exit condition

One complete multi-step E01 Episode executes.

---

# DAY 5 — Trajectories + Runs

**Budget: 5h**

Ship:

- immutable Trajectory;
- Step;
- RunManifest;
- JSONL artifact store;
- Episode runner;
- batch runner.

### Exit condition

```bash
pearl run E01 --policy baseline --partition search
```

produces inspectable artifacts.

First major checkpoint.

---

# DAY 6 — Evaluation vectors

**Budget: 5h**

Ship:

- Evaluator protocol;
- deterministic Evaluators;
- task success;
- grounding;
- tool use;
- compliance;
- escalation;
- efficiency;
- optional Reward aggregation;
- legacy Gnomon Judge adapter.

### Exit condition

One Run produces a decomposed Evaluation Vector.

---

# DAY 7 — Gnomon integrated decision layer

**Budget: 6h**

Ship:

- existing bootstrap;
- existing power;
- paired metric comparison;
- hard-gate regression;
- Judge Calibration:
  - Cohen κ;
  - Krippendorff α;
  - Spearman;
  - bucketed agreement;
- Verdict object;
- statistical tests against references.

### Exit condition

```bash
pearl compare P0 P1
```

returns a structured Gnomon verdict.

Do not rush this day.

---

# DAY 8 — Failure Distribution

**Budget: 5h**

Ship:

- Failure entity;
- taxonomy;
- deterministic failure mapping;
- aggregate distributions;
- conditional slicing;
- CLI.

### Exit condition

```bash
pearl failures <run>
```

shows both unconditional and sliced failures.

---

# DAY 9 — Hill-Climber

**Budget: 6h**

Ship:

- PolicyConfig;
- Candidate;
- mutation protocol;
- bounded neighborhood;
- search partition;
- validation partition;
- confirmation partition;
- stopping rules;
- Gnomon confirmation.

### Exit condition

A deliberately weak deterministic baseline improves through at least one successful hill-climb.

---

# DAY 10 — E01 flagship Gold

**Budget: 6h**

NO NEW FRAMEWORK FEATURES.

Make E01 excellent.

Ship:

- >=8 Seed Scenarios;
- >=6 Mutators;
- >=150 generated scenarios;
- baseline;
- improved candidate;
- failure regime;
- full Search/Validation/Confirmation experiment;
- polished HTML report;
- reproducible walkthrough.

### Exit condition

Five-minute PeaRL demo works end-to-end.

At this point PeaRL should already be resume-worthy.

---

# DAY 11 — Gold environments G2 + G3

**Budget: 5h**

Ship:

E07 Healthcare Investigation.

E13 Retail Compliance.

Both Gold.

The purpose is not fancy docs.

The purpose is attacking the abstraction.

### Exit condition

No special-case framework code required.

---

# DAY 12 — Gold environments G4 + G5

**Budget: 5h**

Ship:

E19 Manufacturing Operations.

E25 Transportation Planning.

Run all five Gold environments through common framework.

### Exit condition

```text
5 / 5 Gold executable
25 / 25 Registry
```

---

# DAY 13 — FieldOS People Engine

**Budget: 6h**

Ship:

- Next.js app;
- SQLite;
- Person;
- Interaction;
- Person dossier;
- Interaction capture;
- Coffee Chat Prep;
- selected-interaction synthesis;
- optional SynthesisProvider interface;
- privacy-safe defaults.

Use synthetic data.

### Exit condition

A 60-second prep brief is actually useful.

---

# DAY 14 — FieldOS Engagement + full RC

**Budget: 6h**

Ship:

- Engagement;
- Objective + ACTRW;
- draft PeaRL export;
- Pattern;
- Impact;
- integration demonstration;
- README passes;
- clean installation;
- screenshots;
- release docs.

Tag:

```text
PeaRL v1.0.0-rc1
FieldOS v0.5.0-rc1
```

Core sprint ends.

Do not casually extend it.

---

# 37. DAYS 15–30 BUFFER PLAN

Buffer is for making good work exceptional.

It is NOT permission to double scope.

---

# DAY 15 — adversarial architecture review

Pretend the framework is bad.

Attack:

- abstraction leaks;
- duplicated concepts;
- hidden environment assumptions;
- test brittleness;
- confusing APIs.

Fix.

---

# DAY 16 — statistical audit

Audit Gnomon.

Questions:

- Are methods paired correctly?
- Are intervals interpreted correctly?
- Is power analysis being applied to the right design?
- Are Hard Gates deterministic?
- Are invalid experiments rejected?
- Are uncertainty claims precise?

No new method merely because it sounds sophisticated.

---

# DAY 17 — OSS install test

Fresh machine/environment.

Follow README literally.

Target:

```text
clone
→ install
→ first E01 result

< 10 minutes
```

---

# DAY 18 — Enterprise-25 Bronze batch 1

Upgrade:

E02–E06 where not Gold.

Five Bronze.

---

# DAY 19 — Bronze batch 2

Five more.

---

# DAY 20 — Bronze batch 3

Five more.

---

# DAY 21 — Bronze batch 4

Remaining Bronze.

Target:

```text
5 Gold
20 Bronze
25 Registry
```

---

# DAY 22 — real LLM dogfood

Use one real provider.

Run a constrained subset of E01.

Do not make live-provider behavior a CI dependency.

Document what deterministic simulation captures versus what real LLM execution exposes.

---

# DAY 23 — FieldOS privacy hardening

Attempt to accidentally leak:

- private records;
- hidden fields;
- local DB;
- exports.

Fix all unsafe defaults.

---

# DAY 24 — PeaRL methodology document

Write:

```text
docs/methodology/why-environments.md
```

Explain:

- why isolated prompts are insufficient;
- environment distributions;
- trajectory-level behavior;
- conditional failure analysis;
- search versus confirmation;
- statistical validation.

---

# DAY 25 — Gnomon methodology

Write:

```text
docs/methodology/gnomon.md
```

Explain:

- uncertainty;
- power;
- paired comparisons;
- Judge calibration;
- hard gates;
- experiment validity;
- known limitations.

Preserve Gnomon's intellectual identity.

---

# DAY 26 — FieldOS UX hardening

Make the core workflows fast.

Do NOT add features.

Reduce clicks.

Improve forms.

Improve empty states.

---

# DAY 27 — related-work analysis

Create:

```text
docs/related-work.md
```

Compare PeaRL honestly to:

- eval runners;
- benchmark frameworks;
- agent tracing/observability;
- prompt optimizers;
- general RL environments.

Answer:

> What is genuinely different?

No strawmen.

---

# DAY 28 — external review

Give project to 2–3 strong technical reviewers.

Ask:

1. What do you think this project does?
2. What seems genuinely useful?
3. What seems fake or overclaimed?
4. Where do you lose the architecture?
5. Which abstraction feels wrong?
6. Would you use it?

Fix repeated feedback.

---

# DAY 29 — final release

Tag:

```text
PeaRL v1.0
FieldOS v0.5
```

Update Gnomon README to redirect.

Keep Gnomon history intact.

---

# DAY 30 — portfolio + freeze

Produce:

### 30-second PeaRL pitch

### 2-minute PeaRL pitch

### 5-minute PeaRL demo

### 30-second FieldOS pitch

### architecture diagram

### one technical blog outline

Then STOP.

Review backlog based on evidence.

---

# 38. Release Gates — PeaRL

## Gate 1 — Correctness

Tests green.

---

## Gate 2 — Reproducibility

E01 flagship result reproducible.

---

## Gate 3 — Generality

All five Gold Environments use the same core abstractions.

---

## Gate 4 — Trajectory integrity

Multi-step Episodes yield complete immutable traces.

---

## Gate 5 — Statistical integrity

Gnomon methodology is:

- tested;
- documented;
- design-aware.

---

## Gate 6 — Search / confirmation separation

Final SHIP experiment does not reuse optimization evidence as if held out.

---

## Gate 7 — Failure insight

At least one environment demonstrates:

```text
average metric hides conditional structural failure
```

---

## Gate 8 — Optimization

At least one PolicyConfig improves through a real Hill-Climb.

---

## Gate 9 — Five-minute demo

Works without handwaving.

---

## Gate 10 — OSS usability

Fresh user can install and run documented example.

---

# 39. Release Gates — FieldOS

## Gate 1

Person + Interaction works.

## Gate 2

Coffee Chat Prep is useful in <60 seconds.

## Gate 3

Interaction capture takes <2 minutes.

## Gate 4

Multi-conversation synthesis shows convergences/contradictions.

## Gate 5

Engagement uses canonical O + ACTRW.

## Gate 6

Engagement exports valid draft PeaRL Spec.

## Gate 7

Pattern accepts evidence from People/work/PeaRL.

## Gate 8

Private data is protected by default.

---

# 40. Success metrics

Ignore GitHub stars initially.

---

## PeaRL successful v1

If:

```text
25 Registry environments
5 Gold environments
>=1 flagship 150+ scenario distribution
multi-step Trajectories
6 standard evaluation dimensions
paired Gnomon comparisons
Judge calibration
conditional Failure Distribution
working Hill-Climber
held-out confirmation
HTML report
clean CLI
```

---

## FieldOS successful v0.5

If:

```text
People
Interactions
Coffee Prep
Conversation synthesis
O + ACTRW Engagements
PeaRL export
Patterns
Impact
```

feel fast enough to actually use.

---

# 41. Failure conditions

The project has failed if:

## PeaRL becomes an eval dashboard

Failure.

---

## PeaRL has 25 shallow environments and weak runtime semantics

Failure.

---

## It claims "RL" without an executable improvement loop

Failure.

---

## Hill-climbing repeatedly optimizes against the same eval set and calls the resulting performance statistically confirmed

Failure.

---

## Gnomon uses mismatched statistical tests because a function happened to already exist

Failure.

---

## PeaRL reduces everything to one scalar Reward

Failure.

---

## FieldOS becomes a personal Notion replacement

Failure.

---

## FieldOS takes more engineering time than PeaRL

Failure.

---

## Five different environments require five different framework hacks

Failure.

---

## Microsoft-specific code enters public core

Failure.

---

# 42. Anti-rabbit-hole rules

During Days 1–14:

Any idea not required by this PRD goes to:

```text
BACKLOG.md
```

It can only enter the sprint if:

## A. Release blocker

Committed feature cannot work without it.

## B. Correctness blocker

Current behavior would be wrong or misleading.

## C. Generality blocker

Multiple Gold environments reveal the same missing abstraction.

Everything else waits.

---

# 43. Quality philosophy

"Anthropic/OpenAI-level" for this project does NOT mean:

- giant scope;
- giant model;
- dozens of integrations;
- fancy marketing.

It means:

## Precise abstractions

Environment means something.

Scenario means something.

Trajectory means something.

---

## Reproducibility

Results can be rerun.

---

## Honest experimental design

Search evidence is not confirmation evidence.

---

## Eval the eval

Broken Scenario/Evaluator is treated as its own failure category.

---

## Statistical humility

Say UNDERPOWERED when underpowered.

Say INVALID when invalid.

---

## Conditional analysis

Don't hide behind averages.

---

## Inspectability

A human can inspect the exact Trajectory behind a score.

---

## Honest limitations

Every report and methodology page has a limitations section.

---

# 44. README thesis — PeaRL

Recommended opening:

> **PeaRL is an environment-centric experimentation framework for improving AI agents.**
>
> Define a workflow as an environment, sample the situations the agent can encounter, capture its trajectories, measure where it fails, statistically validate changes with Gnomon, and hill-climb the harness against held-out scenarios.

Then immediately show:

```text
Environment
    ↓
Scenarios
    ↓
Policy
    ↓
Trajectories
    ↓
Evaluation
    ↓
Gnomon
    ↓
Failures
    ↓
Hill-Climb
    ↓
Replay
```

---

# 45. README thesis — FieldOS

Recommended opening:

> **FieldOS is a local-first learning harness for technical field work.**
>
> Turn conversations and messy engagements into structured knowledge, reusable patterns and measurable impact—and export agentic workflows directly into PeaRL environments.

Then:

```text
People ─────┐
            ▼
        FieldOS
            ▲
Work ───────┘
            │
            ▼
         PeaRL
            │
            ▼
        Patterns
            │
            ▼
         Impact
```

---

# 46. Final scope lock

## PeaRL v1 MUST SHIP

- Gnomon migration;
- EnvironmentSpec;
- EnvironmentRuntime;
- Enterprise-25 registry;
- Scenario Distribution;
- Scenario Mutators;
- Search/Validation/Confirmation partitions;
- Policy abstraction;
- legacy Gnomon Agent adapter;
- Episode execution;
- Trajectories;
- Run artifacts;
- Evaluators;
- Evaluation Vector;
- Gnomon:
  - bootstrap;
  - power;
  - paired comparison;
  - Judge calibration;
  - hard-gate validation;
  - Verdicts;
- Failure taxonomy;
- conditional Failure Distribution;
- Hill-Climber;
- five Gold Environments;
- CLI;
- HTML report;
- docs;
- tests;
- reproducible E01 experiment.

---

## FieldOS v0.5 MUST SHIP

- People;
- Interactions;
- Coffee Chat Prep;
- Multi-Conversation Synthesis;
- Engagement;
- canonical O + ACTRW;
- PeaRL draft export;
- Pattern;
- Impact;
- privacy-safe defaults.

---

## NOTHING ELSE

No seventh FieldOS module.

No 25 Gold environments.

No RL training.

No SaaS.

No fancy org graph.

No task manager.

No calendar.

No giant adapter ecosystem.

No premature performance dashboard.

---

# 47. Governing product principle

If forced to choose between:

> one more feature

and

> making an existing abstraction more correct, general, reproducible or inspectable,

choose the latter.

The desired release should feel:

> **deeper than its feature count.**

PeaRL should feel like a serious technical system.

FieldOS should feel almost suspiciously small for how useful it is.

That is the target.
