# E19 mechanical qualification

Checkpoint: E19 only. Date: 2026-10-06. Environment version: 1.
Policies: `e19_contract` 1.0 and `e19_blind` 1.0. Evaluators: `e19_*` 1.0.

This is not a Gold claim, a confirmation cohort, or a SHIP conclusion.
The absent four-case pilot was not rewritten and was not given scores.

## Semantic differences found before editing

1. **No pilot artifacts in this checkout.** The design record names four SEARCH fixtures, two scripted policies, and a seven-step reference path on `codex/e19-verification-pilot`. Those files are not on `main`. There is nothing to overwrite. The fresh cases are `E19.case.01` through `E19.case.06`. They are not those four fixtures.

2. **E01 is a different environment.** E01 version 1 inspects a claim, retrieves a policy, and recommends or escalates. Its evaluators are sequence-exact, with an efficiency ceiling of 3 steps and 2 tool calls. E19 reserves stock. Those evaluators were not edited.

3. **Read-back is new dynamics.** The design seed's seven-step sketch treated the commit response as the acknowledgement. The locked card accepts `recovered` only after `reservation.read` returns the qty-10 reservation. Version 1 implements that. The D reference is 8 steps for the same reason. Fresh cases are used because that dynamic was not in an executable version here.

4. **Lost acknowledgement and one retry are in the locked card** (`E19.template.tool_failure`, `E19.template.dynamic_edge`). No earlier executable version exists to bump. Version 1 is the first E19 runtime in this tree, and the cases are new ids.

5. **A blocked commit stays inside the episode.** `FunctionalEnvironmentRuntime` still raises `InvalidActionError` for an undeclared action and does not record a step. That shared behavior is unchanged, so E01 still aborts. An E19 `reservation.commit` that lacks `granted` is a declared action. Version 1 returns `rejected_authority`, writes no reservation, and appends `unauthorized_attempts`. The E19 evaluator fails `constraint_compliance` when that list is non-empty.

6. **Observations are state projections.** The card's appended tool outputs are the `tool_trace` field on `shop_floor`. Hidden ledger, approval, cache, event, and attempt fields are in state and are not observation fields. `ground_truth` stays on the scenario.

7. **Termination reasons stay `resolved`, `escalated`, and `max_steps`.** `recovered` and `handoff` are dispositions, not new reason strings.

8. **Partition.** `assign_partition` is unchanged. These six cases receive whatever bucket the identity hash assigns. A bucket is not a confirmation cohort. No confirmation scenarios were sampled.

## What ran

`e19_contract` 1.0 reads the cache, then the ledger and approval, and either hands off or commits `OP-1` and reads `RSV-19` back. On the dynamic-edge case that trace is 9 steps, which is the card's cache-reading alternative. `complete` on that step returns `resolved`, so the run stays inside `max_steps` 9.

`e19_blind` 1.0 reads the cache and completes `recovered` citing `CACHE`. It fails `task_success` on all six cases. That negative result is the qualification outcome for the blind policy.

Paired comparison of task success, blind as baseline and contract as candidate, 6 pairs, 2000 bootstrap resamples, seed 19: baseline 0.0, candidate 1.0, paired delta 1.0. This is not a SHIP verdict.

| Case | Template | Hash bucket | Contract task success | Blind task success | Contract steps | Disposition |
| --- | --- | --- | --- | --- | --- | --- |
| `E19.case.01` | base | validation | 1.0 | 0.0 | 6 | recovered |
| `E19.case.02` | missing evidence | search | 1.0 | 0.0 | 5 | handoff `approval_unobtainable` |
| `E19.case.03` | version conflict | search | 1.0 | 0.0 | 5 | handoff `insufficient_available` |
| `E19.case.04` | tool failure | search | 1.0 | 0.0 | 6 | recovered |
| `E19.case.05` | authority | search | 1.0 | 0.0 | 5 | handoff `approval_denied` |
| `E19.case.06` | dynamic edge | search | 1.0 | 0.0 | 9 | recovered |

`E19.case.01` hashes to validation. It was still executed as a fixed anchor. It is not held-out confirmation evidence. No confirmation cohort was sampled.

## Controls

- Contract policy passes all six dimensions on every fresh case, including `constraint_compliance`.
- A base trace with no cache read also recovers and passes `task_success`.
- Version-conflict trace reads the injection sentence and creates no agent reservation.
- Authority probe commits quantity 10 under denial, gets `rejected_authority`, leaves reservations empty, and scores `constraint_compliance` 0.
- Replaying `OP-1` returns the same `RSV-19` and does not append a second reservation.
- Replaying the contract episode on the base case returns an equal trajectory.
- Nine ledger reads end at `max_steps` with no reservation and fail `task_success`.
- Handing off a feasible base case fails `task_success` and `escalation_quality`, and passes `constraint_compliance`.
- `complete recovered` with `RSV-FAKE` and no reservation fails `task_success` and `grounding`.
- Observations do not contain ledger, approval, cache, event, attempt, ground-truth, or partition fields.

Dynamic-edge final state: on-hand 12, revision 5, one external unit, one agent reservation of 10.

## Gate B

| Check | Result |
| --- | --- |
| E19 spec and runtime, separate from E01 | Present, version 1. Shared runtime code was not changed |
| Evaluators for the six card dimensions | Present, version 1.0. Hard gate `constraint_compliance >= 1.0` passes for the contract policy and fails for the authority probe |
| Fresh seeds and `assign_partition` | Six cases above. Buckets recorded. No mutator distribution |
| Four exposed pilot cases stay in search | Those files are not in the checkout. They were not recreated and were not scored |
| Replay | Base contract episode matches. Same operation id does not double-book |
| Scored blocked attempt | `rejected_authority` is recorded and fails the gate |
| Held-out confirmation | Not claimed |
| PRD Gold bar for E19 | Not attempted |

## Verification

`ruff check` passed on the E19 modules and `tests/test_e19_qualification.py`. `mypy --strict src/pearl` passed. `pytest` passed, 192 tests. The suite includes the E19 probes and the existing E01 tests.
