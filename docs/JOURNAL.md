# PeaRL Journal

Milestone and decision log. New entries go at the top.

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
