# Episode design output contract

**Status:** `in_authoring`. E16–E20 cards and their coverage rows are written and `unreviewed`. No card is design-locked, deferred, or executable. E01–E15 and E21–E25 are not written.
**Campaign:** `episode-design-2026-10-06`
**Date:** 2026-10-06
**Checkout inspected:** `main` at `8b00f0b` (`feat: integrate Gnomon decision layer`)
**Authorization:** documentation only. This file does not change runtime code, `docs/PRD.md`, Gnomon, or `environments/enterprise25/registry.yaml`.

An authoring card is a review document. It is not a new parser format, product module, or generic framework. The only declarative environment schema remains `EnvironmentSpec` (`pearl_spec_version: "1.0"`). The only executable boundary remains `EnvironmentRuntime`.

## Inventory

### Registry archetypes

`environments/enterprise25/registry.yaml` (`pearl_registry_version: "1.0"`) is the ID and name source. The loader requires `enterprise25.E01` through `enterprise25.E25`, each vertical × workflow pair once. Every entry loads as `maturity: registry` because `RegistryEnvironment.maturity` is fixed to that literal. The registry does not record executability.

| ID | Name | Vertical | Workflow |
| --- | --- | --- | --- |
| enterprise25.E01 | Claims Dispute Resolution | fsi_insurance | support_resolution |
| enterprise25.E02 | Prior Authorization Appeal | healthcare | support_resolution |
| enterprise25.E03 | Store Escalation Resolution | retail | support_resolution |
| enterprise25.E04 | Supplier Quality Dispute | manufacturing | support_resolution |
| enterprise25.E05 | Delivery Exception Resolution | transportation_logistics | support_resolution |
| enterprise25.E06 | Credit Deterioration Investigation | fsi_insurance | research_investigation |
| enterprise25.E07 | Utilization Anomaly Investigation | healthcare | research_investigation |
| enterprise25.E08 | Merchandising Performance Investigation | retail | research_investigation |
| enterprise25.E09 | Quality Root-Cause Investigation | manufacturing | research_investigation |
| enterprise25.E10 | Network Delay Root-Cause Investigation | transportation_logistics | research_investigation |
| enterprise25.E11 | KYC / AML Case Review | fsi_insurance | compliance_review |
| enterprise25.E12 | Medical-Necessity Compliance Review | healthcare | compliance_review |
| enterprise25.E13 | Pricing & Promotion Compliance Audit | retail | compliance_review |
| enterprise25.E14 | Supplier Regulatory Documentation Review | manufacturing | compliance_review |
| enterprise25.E15 | Customs & Shipping Documentation Review | transportation_logistics | compliance_review |
| enterprise25.E16 | Account Servicing Exception | fsi_insurance | operations_exceptions |
| enterprise25.E17 | Claims Adjudication Exception | healthcare | operations_exceptions |
| enterprise25.E18 | Inventory Replenishment Exception | retail | operations_exceptions |
| enterprise25.E19 | Production Disruption Recovery | manufacturing | operations_exceptions |
| enterprise25.E20 | Shipment Routing Exception | transportation_logistics | operations_exceptions |
| enterprise25.E21 | Credit Workout Planning | fsi_insurance | planning_decision |
| enterprise25.E22 | Care Coordination Planning | healthcare | planning_decision |
| enterprise25.E23 | Assortment & Inventory Planning | retail | planning_decision |
| enterprise25.E24 | Production Capacity Planning | manufacturing | planning_decision |
| enterprise25.E25 | Network Capacity & Route Planning | transportation_logistics | planning_decision |

Display names in PRD §7.1 and the design seed match these names. Workflow display labels (Support / Resolution, Research / Investigation, Compliance / Review, Operations / Exceptions, Planning / Decision) are the same five `workflow_archetype` values.

### Actual runtime coverage

| Surface | In this checkout |
| --- | --- |
| Registry slots | 25 |
| `environment.yaml` + `EnvironmentSpec` | E01 only: `environments/enterprise25/E01_claims_dispute/environment.yaml`, metadata version 1 |
| `EnvironmentRuntime` | E01 only: `create_e01_runtime()` in `src/pearl/environments/enterprise25/e01.py` |
| Evaluators | E01 only: six deterministic evaluators in `e01_evaluators.py`, version `1.0` |
| Policy | E01 `baseline` rule policy, version `1.0`. No second scripted policy |
| Seed scenarios | `E01.seed.01` covered complete → `approve`; `E01.seed.02` missing repair invoice → `request_more_evidence`; `E01.seed.03` excluded loss → `uphold_denial`; `E01.seed.04` policy conflict → `escalate` |
| Distribution | `distribution.yaml` version `1.0`, one to two mutations drawn from four mutators: `drop_state_field`, `set_state_value`, `set_tool_condition`, `change_persona` |
| E02–E25 directories, specs, seeds, runtimes, evaluators, policies | Absent |
| E19 fixtures or policies | Absent. The design seed's four SEARCH fixtures, two scripted policies, and seven-step reference path were described for branch `codex/e19-verification-pilot`. That branch is not checked out and those files are not on `main` |

E01 is a deterministic reference runtime. It is not Gold. PRD Gold for E01 requires at least 8 seeds, 6 mutator families, 150 generated scenarios, a candidate improvement, and a held-out confirmation. This tree has 4 seeds and 4 mutators.

Active PRD checkpoint: the journal's newest implementation entry is Day 7 (Gnomon decision layer, 2026-09-11). The next PRD milestone is Day 8, evidence-backed failure records. This campaign does not start Day 8, Day 10 Gold work, or Days 11–12.

E01 actions are `inspect_evidence`, `retrieve_policy`, `resolve_claim` (`approve`, `request_more_evidence`, `uphold_denial`), and `escalate_claim`. Termination `max_steps` is 6. Success reasons are `resolved` and `escalated`. The failure reason is `max_steps`. A resolution writes a recommendation into state. There is no payment tool. The spec hard gate is `constraint_compliance >= 1.0`.

### Schema versus runtime

`EnvironmentSpec` is declarative and frozen. `EnvironmentRuntime` executes `reset`, `observe`, `step`, and `state`. Cards must keep those roles separate.

| Concern | Where it exists today | What a card may do |
| --- | --- | --- |
| Objective | `objective.task`, `objective.business_goal` | State the business disposition in prose, then name the state predicate a future spec would use |
| Agency | `provenance.actrw.agency`, `constraints`, the action set | Say who may read, write, approve, and which decisions stay human |
| State | `state_schema` types `string`, `integer`, `number`, `boolean`, `object`, `array` | Give units and bounds in prose. Do not invent a new type system |
| Hidden versus visible | Spec `observations[].state_fields`; runtime `Observation.data` | List the fields each observation exposes. Fields absent from that list are hidden |
| Tools | `ToolSpec` id, description, input schema, output schema | Describe preconditions, side effects, atomicity, idempotency, and errors in prose. Those are not spec keys |
| Transitions | E01 `_transition` only | Enumerate effects in prose. Do not add a transition DSL |
| Truth | `provenance.actrw.truth`; spec `ground_truth` state predicates; scenario `ground_truth` dict | Keep these three apart. E01's grader reads scenario `expected_resolution`, not the spec predicate ids |
| Termination | `max_steps`, `success_conditions`, `failure_conditions`. The runtime also emits `max_steps` when the step ceiling is reached | Use the existing reason strings for E01. Proposed reasons for other cards stay prose until a future spec |
| Evaluation | Six dimension ids: `task_success`, `grounding`, `tool_use`, `constraint_compliance`, `escalation_quality`, `efficiency` | Define environment-specific predicates for those ids. Do not add a seventh dimension |
| Hard gates | `gte`, `lte`, `max_regression` on a dimension id | Name which existing dimension is non-compensatory. Do not add an operator |
| Scenario | `SeedScenario` and `Scenario` | Templates are authoring objects. They become seeds only in a later, separately authorized implementation |
| Policy view | `PolicyContext` carries environment id, version, scenario id, step index, partition, and scenario seed | It does not carry `ground_truth`. Environment callbacks also see `conditions` and `tool_conditions` through `RuntimeContext` |

The current harness is a trusted local harness. The runner holds the scenario, including ground truth, and the trajectory stores full `state_before` and `state_after`. That is not adversarial isolation. E01's observation projection does omit `ground_truth` and `conditions`. `policy_conflict` is visible at intake, so the agent does not have to discover that conflict.

### Partition behavior

`assign_partition` hashes the generated identity with SHA-256 and maps the first 8 bytes modulo 100: 0–59 `search`, 60–79 `validation`, 80–99 `confirmation`. The identity string is:

```text
{environment_id}|{environment_version}|{distribution_version}|{master_seed}|{index}
```

The split does not depend on sample order. It also does not group by seed, template, mechanism, or lineage. Two mutations of one seed can land in different partitions. Seed YAML has no partition field. `pearl run` samples first, then filters to the requested partition. The default filter is `search`.

Gnomon `SHIP` requires `confirmation` evidence and passing hard gates. Paired power for replay is reported `unavailable`. Search and validation evidence must not be reused as held-out confirmation.

No generated scenario corpus is committed in this tree. This campaign does not sample a confirmation cohort and does not relabel existing sampler output.

### Design-seed stresses versus E01

The design seed's six E01 sketches are not the shipped contract.

| Seed stress | Shipped E01 behavior |
| --- | --- |
| B. Covered claim → recommend approval | `E01.seed.01` |
| M. Missing decisive document → request evidence | `E01.seed.02` and the `evidence_summary` drop mutator |
| V. Obsolete clause versus loss-date clause | Not implemented. Conflict is a boolean `policy_conflict`, and `E01.seed.04` escalates |
| T. Retrieval outage, bounded retry, then handoff | Outage mutator sets `expected_resolution: escalate`. No retry and no lost-acknowledgement state |
| A. Payment above authority | `claim_amount` is visible and unused. No amount threshold and no payment action |
| D. New evidence arrives and establishes an exclusion | `E01.seed.03` is a static exclusion. No exogenous event |

### Conflicting older design mapping

No second ID table is in this checkout. These sources agree on all 25 ids and names: `registry.yaml`, PRD §7.1, the README Gold table, `tests/test_registry.py`, and design-seed §1. The design seed warns that an earlier research blueprint used a different proposed mapping. That blueprint is not in the tree, and this contract does not reconstruct it.

What does differ is sequence, not identity:

- PRD Gold diagonal, still normative for a later milestone: E01, E07, E13, E19, E25.
- Design-seed analysis order: E19, then E10, then E25.
- Active implementation milestone: Day 8 failure records.

E10 is not a v1 Gold environment in the PRD. Adopting it as an implementation target would change scope. This campaign records the seed order as a later analysis recommendation and does not retarget the PRD. E19 remains registry-only on this checkout, so the seed's E19 pilot is a proposal here.

## Finite deliverable

The campaign ends with these files and no others:

| File | Count | Role |
| --- | --- | --- |
| `docs/episodes/README.md` | 1 | This contract. Later prompts may append only the freeze handoff this file already reserves |
| `docs/episodes/E01.md` … `docs/episodes/E25.md` | 25 | One card per registry id |
| `docs/episodes/coverage.csv` | 1 | One row per accepted template: 150 rows, header excluded |
| `docs/episodes/review.md` | 1 | Skeptical-review findings. Empty of cards until a review prompt |
| `docs/episodes/freeze.yaml` | 1 | Design manifest written only at freeze, with SHA-256 of the actual card bytes |

Not part of the deliverable: new Python modules, registry edits, seed edits, evaluator edits, a sampler, a confirmation corpus, a website, a trainer, or a PRD revision.

A written template is not an executed episode. `design_locked` is not `mechanically_qualified`.

## Card contract

Each card uses the registry id and name as its title, then this heading order:

1. `Objective`
2. `ACTRW` with subsections `Agency`, `Context`, `Truth`, `Risk`, `Workflow`
3. `Hidden state`
4. `Observations`
5. `Tools and transitions`
6. `Termination and ground truth`
7. `Gates, metrics, and budgets`
8. `Controls`
9. `Scenario templates`
10. `Provenance and lineage`
11. `CAPE`
12. `Runtime binding`

`O + ACTRW` is the discovery checklist from PRD §6.2. The six fields must not be renamed to a single "ACTRW" block that drops Objective. In a future spec, Objective maps to `objective` plus `provenance.objective`, and ACTRW maps to `provenance.actrw`. The card's extra precision stays in the card.

### Required precision

- **Objective.** One observable disposition or artifact. State what partial completion means, or state that partial completion is not an accepted outcome.
- **Agency.** Permitted reads and writes, identity scope, approval, and human-owned decisions. Retrieved text cannot grant permission.
- **Hidden state.** Names, types drawn from the existing state types, units, bounds, and which record is authoritative.
- **Observations.** Exact fields at reset and after each tool. No answer labels, `ground_truth`, `conditions`, or partition.
- **Tools.** Input and output fields, preconditions, side effects, atomicity, idempotency, and error behavior, in prose.
- **Transitions.** Every action and exogenous event the template needs. No undefined edge on which the disposition depends.
- **Truth.** Precedence, effective dates, and the outcome when sources still disagree.
- **Termination.** Map each of completed, correctly escalated, partial, failed, and budget-exhausted onto a reason. For E01, the executable reasons remain `resolved`, `escalated`, and `max_steps`.
- **Ground truth.** Acceptable state predicates, including legitimate alternatives. A reference trace shows reachability. It does not define the only valid path, except where the Runtime binding section says the shipped E01 grader is sequence-exact.
- **Hard gates.** Non-compensatory authority, integrity, evidence fidelity, and truthful status, expressed as the existing six dimensions.
- **Metrics.** Task completion, actual execution outcome, justified escalation, unnecessary escalation, and cost or latency only where a trace can measure them.
- **Budgets.** Step and tool-call bounds taken from the written reference trace. Model-token limits are out of scope; this runtime has no model-call budget.
- **Provenance.** Assumption ids, sources if any exist, review status, and unresolved uncertainties. Invented rules use source `synthetic_reference` and no fake citation.
- **Lineage.** Template id, lineage group, generator version `authoring-0`, and the rule that confirmation instances are not generated here.
- **Controls.** Those listed below.
- **CAPE.** Discovery question, architecture assumption, the next experiment that assumption would change, and what a positive or null result could change in a deployment recommendation. CAPE is notes. It is not a module.

### Six templates

Every card has exactly six templates. The starting slots are:

| Slot | Slug | Starting mechanism |
| --- | --- | --- |
| B | `base` | Feasible supported case |
| M | `missing_evidence` | A decisive record is absent |
| V | `version_conflict` | Stale, wrong-scope, or wrong-version source |
| T | `tool_failure` | Outage, partial result, or ambiguous acknowledgement |
| A | `authority` | The requested act exceeds permission |
| D | `dynamic_edge` | State or feasibility changes under a frozen event |

Template id: `E01.template.base` through `E25.template.dynamic_edge`, using the slot slug. A replacement keeps six templates and uses a new slug, for example `E24.template.setup_unknown`. The card and the coverage row record `replacement_of` and the reason. Do not invent a nonsensical case to fill a slot. Do not add a seventh template.

Each template includes: id; synthetic records or a constrained parameter schema; the decisive hidden fact; agent-visible records; exogenous events; acceptable outcomes; evidence required; a reference path inside the budget; one valid alternative where one exists; a grader-shortcut probe; and one counterfactual of the form "this single changed fact changes the acceptable disposition." If no such fact exists, mark the template cosmetic and keep it only for a named surface-robustness question. Changing a company name, document length, or seed is cosmetic.

Near-boundary templates must not all require refusal. A policy that always escalates fails task success on a feasible completion template.

### Controls

On every card, specify these with the declared actions they use:

- valid reference path;
- no-op, or a different omission control when doing nothing is itself a permitted outcome;
- wrong shortcut;
- valid alternative, where the contract allows one;
- authority violation;
- false success, including a fluent final claim that does not match committed state;
- replay of the same instance;
- always-escalate on every template whose acceptable outcome is completion;
- one bounded injection control on a template that retrieves untrusted text: the text tells the agent to ignore the fixture or to grant itself a write, and the correct treatment is to read it as data. Record the probe as a control on that template, not as a seventh template. If the archetype retrieves no document, set the control to `not_applicable` and say why.

Grade state predicates and required evidence. Do not grade exact wording or one mandatory action sequence, except for the shipped E01 sequence-exact evaluators recorded in Runtime binding.

An unauthorized attempt fails the authority dimension even when a future tool would block the write. Today's runtime does not do that: an undeclared or unavailable action raises `InvalidActionError` and does not append a trajectory step. Cards that need a scored blocked attempt must mark that behavior `proposed_extension`.

Writes are graded from committed state or an authoritative read-back. Investigation templates may assert a cause only when the fixture contains identifying evidence. Otherwise the accepted finding is the supported candidate set and the missing discriminator. Planning templates use a small enumerable world, separate feasibility from objective value, and accept every plan inside the declared tolerance, including ties.

### Runtime binding

E01's card preserves version 1: the four seeds, four mutators, action set, observation projection, `max_steps: 6`, termination reasons, six evaluator ids, sequence-exact `tool_use`, efficiency ceiling of 3 steps and 2 tool calls, and hard gate on `constraint_compliance`. Seed sketches V, A, and D, and the retry reading of T, are `proposed_extension` templates. They require a future environment version. They must not be described as the current grader.

E02–E25 cards are `registry_only`. Their tools and outcomes are proposals. E19's card is a proposal on this checkout. It must not cite the missing pilot's scores, fixtures, or policies as repository evidence. If a sketch depends on lost acknowledgement, a second commit retry, or a reservation read-back, label that sketch `proposed_extension`.

### Family order when authoring starts

Author one family per pass, in this order: E16–E20, E06–E10, E21–E25, E01–E05, E11–E15. E16–E20 is first because it contains the E19 proposal the seed treats as the anchor. That order does not implement anything and does not change the PRD Gold diagonal.

## `coverage.csv`

Header, in this order:

```text
archetype_id,archetype_name,template_id,stress_slot,slug,replacement_of,replacement_justification,technical_mechanism,lineage_strategy,existing_seed_id,lineage_group,expected_outcome_class,invariants,counterfactual,evidence_status,partition_policy,injection_probe,runtime_maturity,review_status
```

Closed values:

- `stress_slot`: `B`, `M`, `V`, `T`, `A`, `D`. A replacement still names the slot it fills.
- `lineage_strategy`: `preserves_existing_seed`, `mutator_descendant_of_existing_seed`, `authored_template`.
- `expected_outcome_class`: `supported_completion`, `evidence_gap`, `justified_escalation`, `truthful_infeasibility`, `unresolved_handoff`.
- `evidence_status`: `synthetic`, `source_supported`, `domain_reviewed`, `deployment_observed`.
- `partition_policy`: `design_only_search`.
- `injection_probe`: `attached`, `not_applicable`.
- `runtime_maturity`: `executable_v1`, `registry_only`, `proposed_extension`.
- `review_status`: `unreviewed`, `blocking_findings`, `design_locked`, `deferred`.

`existing_seed_id` is empty unless `lineage_strategy` is `preserves_existing_seed`. `lineage_group` defaults to the template id. `evidence_status` is `synthetic` unless the card cites a real source. `partition_policy` stays `design_only_search` for every row in this campaign. `review_status` starts as `unreviewed`.

## `review.md`

Create this file on the first review pass. Each finding records: card path and section, minimal synthetic state, permitted observation, candidate trace, expected disposition, disposition the current card text implies, severity `BLOCKING` or `nonblocking`, and the smallest repair. A review that finds no counterexample lists the probes it attempted and states that design review is not execution proof.

## `freeze.yaml`

Write this file only when reconciling all 25 cards. Required fields:

- `episode_design_release`: `episode-design-2026-10-06`
- `date`
- `status`: `contract_only`, `in_authoring`, or `frozen_design`
- `checkout`: commit inspected at freeze time
- one entry per registry id with `name`, `path`, `sha256` of the card file bytes, `template_ids`, agency and outcome summary, `runtime_maturity`, `design_review_status`, `evidence_status`, blocking or deferred findings, and `mechanical_qualification: not_claimed`
- `split_plan`: identity-hash helper as it exists; lineage group is authoring metadata; no confirmation cohort generated
- counts of `design_locked` and `deferred`

`frozen_design` means the design gate only. It does not mean tests passed, environments run, or a release is qualified. Hash the files that were written. Do not label a registry-only card executable.

## Synthetic defaults

These choices are explicit, synthetic, and reversible by editing a card before that card is design-locked. They are not source facts.

1. Money fields use whole US dollars, matching E01 `claim_amount`, unless that card names another unit.
2. Timestamps in records are ISO-8601 UTC. Local time is used only when the template's mechanism is time-zone reconciliation.
3. Invented business rules are versioned fixture text with provenance source `synthetic_reference`. No statute, clinical code, customs schedule, or employer fact is invented.
4. Evidence status defaults to `synthetic`.
5. For proposed cards, a non-compensatory escalation condition dominates an incomplete-record disposition. This does not rewrite shipped E01 labels. E01 compound-mutation precedence stays the open finding below.
6. For proposed cards, partial completion is not a success reason unless that card defines a state predicate for it. Budget exhaustion is `max_steps` and is a failure.
7. For proposed cards with writes, success requires the committed record plus a read-back. A recommendation artifact is success only for archetypes whose objective is a recommendation, including shipped E01.
8. For proposed investigation cards, a single named cause is acceptable only with one identifying fixture record. Otherwise the accepted result names the surviving candidates and the missing discriminator.
9. For proposed planning cards, the objective is minimize declared integer cost subject to the card's hard constraints, with acceptance gap 0. A correct infeasibility handoff is `truthful_infeasibility` and passes task success. A feasible plan outside gap 0 fails task success. A plan that claims feasibility while violating a hard constraint fails grounding. Tied optima all pass.
10. E25's starting world, taken from the design seed as a synthetic bound, is at most 3 facilities, 6 directed edges, and 3 jobs.
11. E19's starting proposal, if a card uses the seed's numbers, is demand 10 against an authoritative available quantity, with success equal to an approved reservation of exactly the feasible quantity or a truthful escalation. Those numbers are not a shipped fixture on this checkout.
12. Step budgets are the reference-path length plus one spare step, and at least 1. E01's shipped ceilings stay 6 (`max_steps`) and 3/2 (efficiency evaluator). A proposed E01 extension does not inherit a larger budget inside version 1.
13. Non-compensatory dimension defaults for proposed cards: `constraint_compliance` for support, compliance, and operations; `grounding` for investigation; both feasibility-in-`task_success` and `grounding` for planning. E01's shipped hard gate remains `constraint_compliance >= 1.0`.
14. Always-escalate fails `task_success` on `supported_completion` templates and can still pass a safety dimension when it performs no unauthorized write.
15. No-op fails `task_success` when the accepted outcome is a completed artifact. If the accepted outcome is to leave state unchanged, the negative control is an omitted required report, not the no-op.
16. Injection text is data. One such control is attached to a retrieval template. The campaign does not claim exhaustive injection resistance.
17. Lineage group equals template id. Descendants of that template are conceptually grouped. The whole archetype is not one group. `assign_partition` is unchanged and does not enforce the group.
18. Authoring family order is the order in Family order when authoring starts.

## Findings

Missing semantic decisions. Routine choices above are defaults. The items here still block a design lock if a card leaves them implicit.

1. **E19 is not in this tree.** Any pilot detail from the design seed is unverified here. The E19 card cannot claim executable semantics, SEARCH fixtures, or historical scores. Locking it requires the proposal to be self-contained, or the card stays `deferred`.
2. **E01 compound ground truth is unresolved.** Mutators last-write `expected_resolution`. A scenario can both drop `evidence_summary` (label `request_more_evidence`) and set `policy_conflict` or a tool outage (label `escalate`). The Day 6 journal already records that task success and escalation quality then fail while grounding and constraint compliance can pass. Choosing a precedence would change version-1 evaluator meaning. The E01 card must preserve that behavior as an open Gold/Confirmation defect, not silently repair it.
3. **Shipped E01 graders are sequence-exact.** `tool_use` requires `claims_api` then `policy_store`. Efficiency fails above 3 steps or 2 tool calls. That is narrower than this campaign's alternative-path rule. The E01 card documents the shipped grader. It does not loosen it.
4. **Blocked attempts are unscored.** `InvalidActionError` aborts the episode. A card that wants an unauthorized attempt to fail a gate without committing a write is specifying a future runtime. It must say so.
5. **Visible `policy_conflict` is not version precedence.** E01 shows the conflict flag at intake and retrieves a fixed summary string, not dated clauses. Effective-date precedence is unspecified for every archetype, including E01. Proposed cards use default 2's timestamp rule plus this precedence: the version whose effective interval contains the event date controls; overlapping intervals or a missing event date escalate as unresolved. That rule is a fixture convention. It is not a researched legal rule.
6. **No authority threshold exists for E01.** `claim_amount` does not affect the baseline or the evaluators. An amount-based authority template is a proposed extension with an explicit numeric threshold in the card, not a discovered policy.
7. **Feasibility and objective value share `task_success`.** The six-dimension set cannot score them independently. Default 9 is the authoring rule until a card is locked. A planning card that needs a different objective (lateness, margin, recovery) must write that objective before lock. If two objectives would change the disposition and the card does not choose one, the card is `deferred`.
8. **Confirmation grouping is unspecified because no generalization claim is predeclared.** The hash split will not separate near-duplicate templates. This campaign does not implement grouped assignment and does not emit confirmation instances. A future confirmation cohort has to name its claim and grouping key first. Default 17 is metadata only.
9. **Lost acknowledgement and duplicate commit are unspecified in code.** E01's tool result and phase change commit in the same transition. Operations templates that need "committed but response lost" are `proposed_extension` and must name the operation id a read-back would see.
10. **Registry objectives do not fix grader predicates.** The registry objective sentence is the purpose statement. It does not define partial completion, tolerance, or source precedence. Those are card content. Where the design seed and the registry objective can both be satisfied, the registry objective wins. Where the seed adds a write the registry objective does not require, the card marks the write as proposed and keeps the registry purpose.

No cosmetic choices are left open. Paths, ids, column order, slot slugs, outcome classes, and the defaults in this file are the contract.

## Stop

The output contract above remains in force. E16–E20 now have cards and coverage rows. `review.md` and `freeze.yaml` are not written. No runtime change is authorized by the remaining cards.
