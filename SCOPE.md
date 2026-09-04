# Scope

This file summarizes the PeaRL v1.0 scope lock. The canonical PeaRL + FieldOS
PRD at `docs/PRD.md` remains normative if this summary is incomplete.

## PeaRL v1

PeaRL is an environment-centric experimentation and improvement framework for
AI agents. It will ship:

- declarative `EnvironmentSpec` and executable `EnvironmentRuntime` boundaries;
- reproducible Scenario distributions, mutators, and held-out partitions;
- Policy, Episode, immutable Trajectory, Run, and artifact abstractions;
- decomposed Evaluation Vectors and non-compensatory Hard Gates;
- Gnomon statistical inference, including bootstrap intervals, design-aware
  power reporting, paired comparisons, judge calibration, and Verdicts;
- conditional Failure Distributions;
- bounded PolicyConfig hill-climbing with search, validation, and confirmation
  separation;
- the Enterprise-25 registry, five Gold Environments, a CLI, reports, tests,
  and a reproducible E01 experiment.

## Hard boundaries

PeaRL v1 does not include model-weight training, PPO, GRPO, RLHF, hosted SaaS,
distributed workers, production telemetry, a browser UI, a plugin marketplace,
or a broad provider-adapter ecosystem.

Gnomon remains the statistical decision subsystem. It does not generate
Scenarios, execute environments, optimize PolicyConfigs, or choose the task an
agent should solve.

FieldOS is a separate product. PeaRL must not depend on it.

## Milestone rule

Days 1–14 are incremental. A feature is implemented only when its milestone
requires it. Attractive additions go to `BACKLOG.md` unless they are necessary
for correctness, release, or cross-environment generality.
