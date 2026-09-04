# PeaRL

> Environment-centric experimentation and improvement for AI agents.

PeaRL models real workflows as executable environments, runs agent Policies
against reproducible Scenario distributions, records Trajectories, measures
conditional failures, and uses Gnomon to decide whether an improvement is
supported by evidence.

PeaRL is local-first, provider-neutral, and does not train model weights.

## Status

Day 2 complete. Canonical declarative environment and Scenario models,
actionable YAML validation, and the complete Enterprise-25 Registry are
available. Executable runtimes and Scenario mutation intentionally begin in
later milestones.

## Development

```bash
python -m pip install -e ".[dev]"
pearl --help
pearl registry list
pearl validate path/to/environment.yaml
pytest
ruff check .
mypy src
```

See [SCOPE.md](SCOPE.md) for the locked product boundary and
[ARCHITECTURE.md](ARCHITECTURE.md) for the staged architecture. The complete
specification is in [docs/PRD.md](docs/PRD.md), and implementation progress is
recorded in [docs/JOURNAL.md](docs/JOURNAL.md).

## License

MIT. The Gnomon statistical modules retain attribution to their original
project and license.
