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

## Current package surface

Days 1–2 introduce only the statistical kernel, CLI, declarative specification,
and Registry surfaces:

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
    spec/
        __init__.py
        environment.py
        loader.py
        registry.py
        scenario.py
environments/
    enterprise25/
        registry.yaml
```

Scenario distribution, runtime, Policy, trajectory, evaluator, failure,
optimization, and reporting packages begin in their designated milestones.
