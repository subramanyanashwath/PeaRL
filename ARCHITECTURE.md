# Architecture

PeaRL is built around an explicit sequence:

```text
Environment
    -> Scenarios
    -> Policy
    -> Trajectories
    -> Evaluation
    -> Gnomon
    -> Failures
    -> Hill-Climb
    -> Replay
```

## Boundaries

- `EnvironmentSpec` is declarative and serializable.
- `EnvironmentRuntime` executes state transitions.
- `pearl.spec.Action` and `pearl.spec.Observation` declare the environment
  contract. `pearl.runtime.Action` and `pearl.runtime.Observation` are values
  exchanged during execution; namespace separation prevents declaration from
  becoming mutable runtime state.
- `Policy` is the complete agent system; `PolicyConfig` is its tunable state.
- `Trajectory` is an immutable execution trace. Evaluation records remain
  separate and never mutate historical traces.
- `Evaluation Vector` is primary. A scalar Reward is optional and cannot
  replace decomposed dimensions or Hard Gates.
- `pearl.gnomon` answers statistical questions about evaluation evidence. It
  does not own environment execution, scenario generation, or optimization.
- Search evidence is optimization evidence. Final SHIP evidence comes from a
  held-out confirmation partition.
- File-based Run artifacts are canonical. Existing Gnomon SQLite code may later
  become an optional index or compatibility backend.

## Gnomon migration

Day 1 migrates the statistically tested, self-contained bootstrap and power
modules with their APIs and frozen result dataclasses intact. No rewrite is
performed for naming uniformity.

Legacy Gnomon concepts are preserved for later adapters:

| Gnomon concept | PeaRL boundary | Milestone |
|---|---|---:|
| `Agent` | legacy Policy adapter | Day 4 (shipped) |
| `EvalCase` | Scenario/single-turn compatibility | only if compatibility demand requires it |
| `EvalRunner` | compatibility runner | only if compatibility demand requires it |
| `EvalResult` | one-step Trajectory plus EvaluationResult | only if compatibility demand requires it |
| `Judge` / `LLMJudge` | Evaluator adapter | Day 6 |
| `score_ci` | compatibility aggregation utility | Day 6–7 |
| SQLite storage | optional run index/backend | only if backend demand requires it |

PeaRL core must not depend on these legacy types.

## Runtime and Policy boundary

`EnvironmentRuntime` owns lifecycle and state integrity: `reset`, `observe`,
`step`, defensive state snapshots, action availability, maximum-step
termination, and declared termination reasons. `FunctionalEnvironmentRuntime`
provides that machinery while each Environment supplies two deterministic
callbacks: a state projection and a state transition. Core therefore contains
no E01 branches.

Runtime updates are atomic. The next state and observation are validated before
the internal state, step counter, or termination reason advances. Observations
must faithfully project the fields declared by their corresponding
`Observation` specification, and Policies can choose only actions exposed by
the current observation.

The canonical `Policy` interface is asynchronous because real agent systems are
network-bound. `RulePolicy` and `CallablePolicy` make deterministic synchronous
logic trivial to use. `LegacyGnomonAgentPolicy` adapts Gnomon's structural
`Agent.run(input: str) -> str` contract without adding a dependency on the
Gnomon package; environment-specific output parsing remains explicit.

Neither `RuntimeContext` nor `PolicyContext` contains Scenario Ground Truth.
Ground Truth belongs to evaluation, not action selection. Runtime transitions
surface tool calls and results as execution evidence without making the generic
Episode runner inspect environment-specific state.

## Trajectory and Run evidence boundary

`Step`, `Trajectory`, `PolicyReference`, and `RunManifest` are strict,
serializable evidence records. A Step snapshots the pre-action state,
policy-visible observation, selected action, optional tool exchange, post-action
state, and latency. Snapshot containers are recursively frozen, Step indexes are
contiguous, and adjacent states must agree. Evaluation remains a separate record
and cannot mutate a historical Trajectory.

Episode IDs are derived from complete behavioral evidence. Run IDs cover the
entire evidence bundle: Environment version, ordered full Scenario records,
partition, sampling seed, Policy identity/configuration hash, and resulting
Trajectories. Repeating the same deterministic Run is therefore idempotent;
stochastic outcomes receive distinct identities, while changed content under an
existing identity is rejected as a collision.

The batch runner preserves Scenario order and creates a fresh runtime per
Episode. The canonical artifact store writes `manifest.json`, `scenarios.jsonl`,
and `trajectories.jsonl` to a staging directory and publishes the complete Run
with one atomic rename.

## Evaluation boundary

An `Evaluator` is a versioned function from one Trajectory and its Scenario to
one normalized `EvaluationResult`. Evaluators receive Ground Truth, while the
Policy and runtime never do. PeaRL checks result attribution against the invoked
Evaluator so mislabeled dimensions, versions, Scenario IDs, or Trajectory IDs
cannot enter a vector.

An `EvaluationVector` preserves decomposed results in a fixed order. A Run-level
`EvaluationBundle` applies one versioned Evaluator suite to every Episode in
manifest order. The artifact store atomically attaches those vectors as
`evaluations.jsonl`; existing Run and Trajectory bytes remain unchanged, and a
different evaluation under the same Evaluator versions is rejected rather than
silently overwritten.

Reward is optional. It can be computed only from a complete vector with
explicit, non-negative weights that sum to one; it never replaces the vector or
Hard Gates. The legacy Gnomon Judge adapter requires an explicit
Scenario-to-case mapping and preserves Gnomon's synchronous score contract
without importing the legacy package.

E01 owns its deterministic semantics for task success, grounding, tool use,
constraint compliance, escalation quality, and efficiency. Core owns the
contracts and orchestration, not claims-specific scoring rules.

## Scenario generation boundary

Seed Scenarios are human-authored reference cases. A Scenario Distribution
selects a seed and applies a bounded sequence of versioned `ScenarioMutator`
implementations. A semantic mutation may carry a corresponding Ground Truth
repair; the original Scenario remains unchanged.

Sampling derives an independent random stream for each output index from the
environment version, distribution version, caller seed, and index. Partition
assignment hashes the same stable identity into fixed 60/20/20
Search/Validation/Confirmation bands. It does not depend on requested batch
size, so extending a sample preserves both prior Scenarios and their labels.

The partition label is evidence provenance, not a convenience split. Future
optimization may read Search and Validation cases, but only Confirmation cases
may support the final Gnomon SHIP decision.

## Current package surface

Days 1–6 introduce the statistical kernel, CLI, declarative specification,
Registry, Scenario distributions, Runtime, Policy, execution evidence, and
evaluation surfaces:

```text
src/pearl/
    __init__.py
    cli/
        __init__.py
        app.py
    gnomon/
        __init__.py
        bootstrap.py
        power.py
    environments/
        enterprise25/
            e01.py
            e01_evaluators.py
    evaluators/
        adapters.py
        base.py
        deterministic.py
        runner.py
    policies/
        adapters.py
        base.py
        callable.py
        rule.py
    runtime/
        artifacts.py
        environment.py
        episode.py
        models.py
        runner.py
    scenarios/
        __init__.py
        distribution.py
        mutators.py
        partitions.py
    spec/
        __init__.py
        evaluation.py
        environment.py
        loader.py
        registry.py
        scenario.py
        trajectory.py
environments/
    enterprise25/
        registry.yaml
        E01_claims_dispute/
            environment.yaml
            distribution.yaml
            seeds/
```

Failure, optimization, and reporting packages begin in their designated
milestones.
