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
| `Agent` | legacy Policy adapter | Day 4 |
| `EvalCase` | Scenario/single-turn compatibility | Day 4 |
| `EvalRunner` | compatibility runner | Day 4 |
| `EvalResult` | one-step Trajectory plus EvaluationResult | Day 5–6 |
| `Judge` / `LLMJudge` | Evaluator adapter | Day 6 |
| `score_ci` | compatibility aggregation utility | Day 6–7 |
| SQLite storage | optional run index/backend | Day 5 |

PeaRL core must not depend on these legacy types.

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

Days 1–3 introduce the statistical kernel, CLI, declarative specification,
Registry, and Scenario-distribution surfaces:

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
    scenarios/
        __init__.py
        distribution.py
        mutators.py
        partitions.py
    spec/
        __init__.py
        environment.py
        loader.py
        registry.py
        scenario.py
environments/
    enterprise25/
        registry.yaml
        E01_claims_dispute/
            distribution.yaml
            seeds/
```

Runtime, Policy, trajectory, evaluator, failure, optimization, and reporting
packages begin in their designated milestones.
