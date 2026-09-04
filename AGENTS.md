# PeaRL repository instructions

The canonical product specification is `docs/PRD.md`.

- Treat its Canonical Terminology, Scope Lock, engineering budget, daily
  milestones, and release gates as normative.
- Inspect existing implementation before changing code.
- Implement only the active daily milestone. Do not begin future-day features
  early.
- Put attractive but non-required ideas in `BACKLOG.md`.
- Preserve Gnomon's tested statistical primitives and their attribution.
- Do not conflate `EnvironmentSpec` with `EnvironmentRuntime`.
- Do not reuse search or validation evidence as held-out confirmation evidence.
- Run tests, lint, and strict type checking before completing a milestone.

## Work log

Update `docs/JOURNAL.md` with every substantive implementation session. Add the
newest entry at the top and record:

- date and milestone;
- what shipped;
- verification performed and exact results;
- deviations from the PRD;
- unresolved architecture or correctness concerns;
- the next bounded milestone.

Keep entries factual and concise. Version control records file-level changes;
the journal records decisions, evidence, and milestone state.
