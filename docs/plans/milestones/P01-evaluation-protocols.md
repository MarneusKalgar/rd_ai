# P01 — Evaluation protocols and model fundamentals

- Version: **1.1**.
- Created: **2026-10-31**.
- Status: **S01–S07 concluded 2026-11-01; C01 judge calibration unselected**.
- Parent: [project roadmap](../../roadmap.md#p01--evaluation-protocols-and-model-fundamentals).
- Planning baseline: `50d4e4d` — P00 and S08 concluded.

## 1. Outcome and first selected question

Make the next research decision inspectable before it runs: define its data,
exposure, comparator, changed factors, rubric, metrics, numeric thresholds,
resource limits and failure policy. Extend the existing evaluation application
only where it cannot yet enforce or report that protocol.

The first selected protocol is **P01-E01, offline comparison verification**:

> Can the evaluator produce a complete, traceable paired comparison and detect
> misleading improvement caused by omitted failures, extra rows, null-heavy
> agreement, mixed execution settings or unsupported acceptance claims?

Use saved native Gemma v1/v2 `baseline-16384` results as the comparison rehearsal,
subject to exact comparability checks. This adds a verified comparison/reporting
capability; it is not a fresh model experiment or independent confirmation of
v2's quality. Include all thirty inputs for operational reporting and only the
ten approved gold cases for factual scores. Keep all failed outcomes.

P01-E01 requires **zero model calls, zero generated tokens and $0 additional API
spend**. Cached public archives or explicit Garage retrieval supply evidence.
No additional customer documents are assumed available. A useful negative
comparison is a valid result; a broken evaluation control is not a passed gate.

## 2. Inherited evidence and actual gaps

| Surface | Reuse | P01 addition |
| --- | --- | --- |
| Approved data | Thirty neutral texts, ten human-approved gold POs, existing source/layout groups and hash chain in `data/corpus-manifest.json` and `data/manifest.json` | Separate exposure/protocol metadata; no edits to frozen manifests or labels |
| Scoring | `evaluation/scoring.py`: exact values, positional rows, extra-row penalties, header/line and present/null counts, failed output earns zero matches | Paired case/field transitions and versioned error labels without changing the primary scorer |
| Run verification | `evaluation/reporting.py`: terminal records, manifest/input/schema identities, variant grouping and overlap rejection | An explicit selected population, permitted differences and comparison eligibility checks |
| Operations | `evaluation/metrics.py`: retry-inclusive populations, unknown charges, latency sample counts and local-cost exclusions | Matched-population deltas and explicit non-comparability where identities or populations differ |
| Assisted workflows | Existing correction/split evaluators and source-support reports retain prior/final outputs, rejected changes, unknown support and reconstructed timings | Shared rubric terminology and reporting contract; adapt existing outputs only where needed, not another execution harness |
| Reproduction | Ledger-free reproduction of 240 observations/eight variants, archive verification and Garage restore | Preserve those outputs and bind new analysis to original evidence |
| Verification | P00-S08 recorded 956 passing tests, lint/types/gold/preflight, preserved storage and exact report reproduction | Focused new behavioral controls plus the appropriate complete implementation gate |

See [evaluation rules](../../reference/evaluation.md),
[section 9 verification](../../reports/section9-verification.md),
[identifier correction](../../reports/identifier-correction.md) and
[header/line splitting](../../reports/gemma-header-lines.md). Their measurements
remain inherited, with their original limitations and conditions.

The twenty non-gold cases remain unlabeled. Gold10 has repeatedly informed
development. Neither the remaining twenty nor a new split of the ten becomes
a blind holdout merely through a new directory, timestamp or experiment ID.

## 3. Scope and invariants

In scope: protocol/exposure metadata, error and review rubrics, paired saved-run
analysis, controlled regression/challenge fixtures, model-fundamentals notes,
model-free CLI/Make integration, tests and reproducible evidence.

Excluded from mandatory P01: new extraction runs, prompt/model/sampling sweeps,
Qwen reinstall, Docker Ollama setup, fine-tuning, workbook parsing, new source
selection/cropping/chunking, a production support classifier, routing, retrieval,
agents/MCP, an approval UI, automatic correction and deployment. These require
their own selected question and later milestone scope. Judge calibration is
conditional, not a default dependency.

| Invariant | Requirement |
| --- | --- |
| Output contract | Preserve PO v1 and its exact scorer; no second handwritten PO model or silent normalization/alignment/repair |
| Factual authority | Only existing approved gold or separately reviewed/versioned future labels support factual accuracy; predictions and agent annotations are not gold |
| Evidence | Preserve original records, run IDs, hashes, failures, sampling aliases, archive formats and unknown-charge holds |
| Runtime | Python, dependency work and substantial scripting in Docker; canonical Make targets; `DI_*` settings and existing external storage identities |
| Isolation | Offline evaluation has no model dependencies or provider settings and never initializes or modifies a ledger |
| Privacy | No private workbooks, mappings, settings, ledger backups or recovery copies enter fixtures, Git, images, provider requests or public proof |
| Authorization | A draft/implemented protocol grants no inference or spending authority; future paid invocations need their concrete approved commands and allowances |

Implementation stays inside the existing application, primarily
`src/extraction_service/evaluation/` and its CLI integration. Add cohesive
modules for new responsibilities when needed; do not create a generic evaluation
framework, second dependency environment, database or plugin system.

## 4. Ordered implementation slices

### P01-S01 — Inventory evidence and freeze P01-E01

1. Record the implementation revision and available pinned archives, run hashes,
   exact input IDs, schema/prompt/model/runtime identities and approved labels.
   Resolve cache absence through the existing retrieval workflow; never rerun a
   model to replace missing evidence.
2. Create a sidecar exposure inventory for all thirty inputs. Reference original
   manifest hashes and source/layout groups. Record known uses in screening,
   prompts/examples, diagnostics, output inspection and manual review. Retain
   `unknown` where history cannot establish exposure; do not assert unseen data.
3. For any proposed split, keep every shared source **and** shared layout family
   together. If these relations connect several cases transitively, they remain
   one group. Unknown grouping blocks an independence claim, not development
   analysis. Do not force artificial train/test partitions into this small set.
4. Write the P01-E01 protocol before collecting its new analysis. Bind the saved
   native v1/v2 baseline variants and exact thirty-input membership. Permit the
   prompt identity as the intended changed factor. Verify runtime/digest,
   representation, context, thinking, sampling, output allowance and execution
   controls; record collection-time differences. This is a historical paired
   comparison, not randomized causal evidence.
5. Freeze expected control outcomes and the thresholds in section 6. Record
   question, owners/review status, exposure/rubric versions, archive identities,
   output destinations and zero-inference limits. A material revision gets a
   new version/hash before evaluation, with its reason retained.

**Accept S01:** all thirty inputs have traceable label/exposure/group status;
the exact selected comparison and permitted differences are recorded; nothing
is promoted to independent evaluation or new human approval. Missing evidence
or incompatible variants are explicit blockers for that comparison.

### P01-S02 — Version the error, no-change and abstention rubrics

1. Define mechanical error categories using existing validation and mismatch
   paths: unusable/failed output, wrong header, wrong line field, present/null
   error and extra/missing row. Report an order/selection cause only when fixture
   truth or reviewed evidence establishes it; positional mismatches alone do
   not. Retain raw paths and original statuses. Semantic cause may remain
   `unreviewed` or `unknown`.
2. Distinguish exclusive primary outcome counts from overlapping diagnostic
   tags. Publish category populations so one error with several tags cannot
   inflate a claimed total. Correct/incorrect, source support and permission
   to apply a proposal are separate dimensions.
3. Define review outcomes outside PO objects: change warranted, no change
   warranted, insufficient evidence/abstain and not reviewed. Preserve the
   proposed, retained and original objects plus the decision's evidence.
   A model refusal, all-null output or parser failure is not a successful
   abstention and receives no rescued factual matches.
4. Define unnecessary change as altering a reviewed-correct unit, harmful change
   as correct-to-wrong, and false support/acceptance as claiming support or
   acceptability for a reviewed-wrong unit. Unknown/unreviewed units are not
   counted as correct or negative anchors. Human authority to apply a change
   remains a later application capability.
5. Give each rubric an evidence requirement and review status. Existing gold
   supports exact mismatch judgments only. Source-grounding/no-change judgments
   need their own explicit anchor or human review; never infer them from the
   provider agreeing with itself. Unreviewed proposed anchors remain unusable
   for factual acceptance rates.

**Accept S02:** each reported decision/error has a versioned definition, unit,
population and evidence status. A rubric can be reviewed without changing gold;
an unresolved semantic judgment stays unknown and cannot inflate accuracy.

### P01-S03 — Implement protocol validation and evidence binding

1. Add strict versioned metadata for the protocol, exposure references, rubric
   references, allowed differences, selected cases, thresholds, resource bounds
   and output policy. Pydantic validates operational metadata, not a duplicate
   PO schema. Store project-relative public paths and explicit hashes.
2. Reuse corpus loading, verified archives/terminal records, variant identities,
   sampling aliases and manifest-bound evaluation policy. Reject changed or
   missing hashes, duplicate cases, overlapping repeats and unlisted variants.
   Repetitions need explicit identities rather than accidental aggregation.
3. Validate comparison membership against the protocol before calculating
   deltas. Never silently intersect two unequal input sets, drop failed cases,
   normalize additional settings or introduce a new sampling alias to force a
   match. A missing terminal record differs from a terminal not-attempted record.
4. Add a model-free validation entrypoint and a planned experiment-evaluation
   entrypoint through the existing application/Make structure. Proposed names:
   `make validate-evaluation-protocol` and `make evaluate-experiment`, with an
   explicit `--protocol` and evidence/output selection. The implemented commands and exact arguments are documented in the
   [operating guide](../../guides/evaluation-protocols.md).
5. Keep original evidence read-only, write only a separate ignored analysis
   directory, and refuse conflicting output replacement. Persist protocol,
   rubric, exposure and source identities in the result.

**Accept S03:** a valid offline protocol resolves deterministically; each
single-defect protocol/evidence case fails at the intended boundary. CLI tests
prove no additional HTTP requests, model setup or accounting writes occur.

### P01-S04 — Add paired comparisons and review-aware reporting

1. Pair by approved input identity within the predeclared variant selections.
   Emit each case's before/after primary counts, exactness, validity, header/line
   counts, present/null subsets, extra/missing rows, original paths and failures.
   Preserve all thirty operational cases and mark the twenty factual scores
   unavailable; factual deltas use the same ten approved cases on both sides.
2. Preserve current aggregate scoring: sum matches and denominators before
   dividing, including extra rows. Display both denominators and the accuracy
   difference in percentage points; do not imply that unequal primary
   denominators are a fixed set of field trials.
3. On **gold field paths only**, report wrong-to-correct, correct-to-wrong,
   both-correct and both-wrong transitions. Missing/invalid output is wrong,
   including gold-null fields. Extra predicted rows are excluded from that
   transition grid but remain penalized in the primary score and separate row
   deltas. Do not rematch, reorder or deduplicate rows to improve transitions.
4. Where reviewed decision anchors exist, report no-change correctness,
   unnecessary/harmful changes, false support/acceptance, abstention and review
   coverage with explicit numerators/denominators. Empty anchor populations
   yield unavailable rates, not zero errors or 100% success. Do not gate or
   alter production outputs using these offline judgments.
5. Reuse operational accounting and timing definitions. Separate added calls
   from reused evidence, component timings from reconstructed totals and live
   end-to-end measurements. Unknown billed cost stays unknown; local API cost
   zero excludes machine, electricity and review time. Report measured review
   time only when recorded, otherwise leave it unavailable.
6. Keep all selected outcomes visible when a comparison is ineligible; explain
   why no paired conclusion is available. Descriptive per-group/case results
   must not become confidence claims about unseen layouts from ten reused cases.

**Accept S04:** independently hand-counted fixtures reconcile case transitions,
primary totals, row penalties and review populations. Mixed controls and
selective omission cannot produce an accepted improvement claim. Existing
evaluations and historical report reproduction remain unchanged.

### P01-S05 — Build deterministic regression and adversarial challenges

1. Add small synthetic fixture pairs and verified saved-output cases covering
   the controls in section 6. Keep synthetic fixtures outside the approved
   `data/` corpus, for example under `tests/fixtures/evaluation/`; declare their
   origin, expected behavior, hashes and exposure separately.
2. Pair benign document content with an injected instruction to change the
   extraction policy or evaluation verdict. Use fictional text and controlled
   outputs. Verify data remains untrusted input to the actual validation,
   persistence and reporting boundaries; do not execute document instructions.
3. Add harmless cross-case/context markers and system-instruction disclosure
   probes. Keep legitimate requested document values distinct from markers
   belonging to another case or internal test context. Prompts are not a secret
   store or authorization mechanism. Record marker disclosure separately from
   unauthorized effects; an offline fixture cannot measure real model obedience.
4. Exercise hostile but schema-valid string values through existing JSON/export
   boundaries. Strings are data, not executable code or an acceptance verdict.
   Do not add a browser, spreadsheet executor, shell/tool adapter or endpoint
   merely to demonstrate a risk that this application cannot currently reach.
   Renderer/formula-specific protection belongs with that later consumer.
5. Reuse bounded admission/retry/deadline/accounting controls for controlled
   oversized/failed requests, including unattempted cases and unknown charges.
   No real long generation or denial-of-service experiment is required.
6. Test through real loaders/CLI/reporting boundaries as appropriate, with
   independent expected numbers. Add bounded mutations only where an assertion's
   sensitivity remains uncertain; require the intended failure and restore the
   disposable copy afterward. Do not write a second implementation as the oracle.

**Accept S05:** every selected deterministic control has a passing legitimate
case and an observed intended failure/flagged condition. Model-dependent attack
success, leakage resistance and later consumer safety remain unmeasured.

### P01-S06 — Execute offline P01-E01 and explain the fundamentals

1. Freeze the implemented protocol/rubric/fixture versions, then run P01-E01
   once from verified saved sources. Retain the complete paired report and
   negative-control outcomes. A failed gate is investigated, not reclassified
   as a successful candidate or silently excluded.
2. Produce a concise reference note connecting saved observations to tokens,
   context admission versus output allowance, thinking/reasoning token use,
   truncation, temperature/top_p, structured validity and factual correctness.
   Use the recorded 4,096/8,192/16,384 output and native-context experiments;
   new sweeps or current provider capability guarantees are not needed.
3. Explain why larger context, more output, a valid schema, a cloud label or a
   model's nominal size does not establish task reliability. Distinguish native
   hardware acceleration from Docker CPU observations without claiming a newly
   measured speed ratio or unpublished provider parameter counts.
4. State what the paired saved evidence supports, what remains unknown and
   what concrete P02 experiment could use the protocol next. Any new factual
   quality/adoption thresholds and model/resource choices belong in that
   experiment's predeclared record, not retroactively fitted to these results.

**Accept S06:** P01-E01 meets the deterministic thresholds below, all selected
outcomes remain inspectable, and fundamentals are explained with inherited
evidence rather than a new model run or repeated-model-family conclusion.

### P01-S07 — Verify, archive and hand off

1. Run focused implementation checks, then `make check` for the completed
   behavior change. Use the resulting count, not a required increase over 956.
   Run the existing model-free report reproduction once after evaluation changes.
2. Reproduce the new comparison from an isolated public-source/evidence export
   without private environment files, ledger/backups or original results. Reject
   a deliberately altered metric or protocol/source hash with the intended
   failure. Record reused Docker/host caches honestly.
3. Archive detailed public analysis/control logs through the existing workflow;
   upload/full-GET verify and isolated restore when using Garage. Version only
   the protocol/rubric/case metadata, compact archive references, guide/report
   and source/tests. Raw reports and logs stay ignored. Existing evidence is
   never rewritten to absorb P01's extra metadata.
4. Record implemented/inherited/unexercised coverage, unknown labels/review
   populations, decision and remaining limits. Update the roadmap status only
   after the gates pass. Explicitly hand off the next selected question to P02
   or another milestone; do not automatically schedule model experiments.

**Accept S07:** the new analysis and inherited baseline reproduce from declared
public inputs; preservation, negative controls and archival are verified. P01
completion describes evaluation capability, not new extraction reliability.

### P01-C01 — Conditional judge calibration, separately selected

Do not implement or run a judge merely to cover a roadmap topic. Select this
only if a concrete judgment cannot be usefully resolved by exact comparison,
source evidence or a practical reviewed rubric.

Before work: identify the judge's narrow decision unit, reviewed positive,
negative and abstention anchors, calibration/evaluation exposure, baseline,
disagreement and false-acceptance metrics, numeric thresholds, route/prompt
identity and bounded calls/tokens/time/cost. Freeze those before measurement.
Resolve disagreements through explicit human review; never make the judge's
output its own reference answer. JEV is a deferred candidate, not the default.

No reviewed anchors or no separately approved invocation means no judge study.
Its conclusion may be reject/defer/inconclusive. It neither blocks mandatory
P01 completion nor grants automatic acceptance authority to a future judge.

## 5. Planned artifacts and interfaces

The following responsibilities were delivered for the selected scope. Protocol
metadata is under `config/evaluation/`; tests use controlled inline fixtures and
shared approved-file fixtures, with a bound control selector inventory in config.
No separate synthetic PO corpus or second execution harness was introduced.

| Location | Responsibility |
| --- | --- |
| `config/evaluation/` | Versioned protocol, exposure inventory and rubric; P01-E01 and exact public evidence bindings |
| `src/extraction_service/evaluation/` | Strict metadata loading, comparison eligibility, paired/error/review reporting; reuse scorer and run verification |
| Existing application CLI and root Makefile | Model-free protocol validation and experiment evaluation |
| `tests/application/test_evaluation_protocol.py` and `config/evaluation/control-suite-v1.json` | Controlled fixtures, independent arithmetic/decision oracles, bound control selectors and process-level negative controls |
| `docs/reference/` and `docs/guides/` | Metric/rubric definitions, saved-observation fundamentals and exact offline commands |
| `docs/reports/P01-evaluation-protocols.md` | Actual outcomes, review status, decision, limits and archive links |
| Ignored `results/` plus compact `archive-index/` | Full analysis/logs, preserved originals and verified public proof |

An evaluation protocol is not an execution permission file. It must not add
`--allow-provider`, initialize budget, load a model or send requests as a side
effect of validation, analysis, reproduction or archival.

## 6. P01-E01 thresholds and resource policy

These thresholds validate the evaluation capability on a finite declared suite;
they are not production accuracy or security guarantees.

| Gate | Predeclared pass criterion |
| --- | --- |
| Data/exposure inventory | 30/30 cases have group, label and exposure status; unknown history remains explicit; no false independent/approved-label claim |
| Pair membership | Exactly the declared 30 cases on each eligible side; factual populations exactly the same approved gold10; no omitted failures or automatic intersection |
| Provenance/control eligibility | Every selected identity/hash/control passes; missing, changed, duplicate or non-permitted differences block the comparison |
| Arithmetic | All selected hand-counted fixture totals/transitions/rates match exactly; no tolerance-based acceptance of wrong integer populations |
| Required control suite | All 16 controls below produce their predeclared outcome, with legitimate positive counterparts; zero observed false acceptance of a known-bad control |
| Review-aware metrics | Every claimed factual/semantic decision has the appropriate approved or reviewed anchor; absent anchors yield unavailable metrics |
| Historical baseline | Existing 240-observation/eight-variant evaluation and report tables reproduce unchanged |
| Implementation/isolation | Relevant checks and full offline gate pass; zero inference/accounting writes; private exclusions and evidence preservation hold |

Required control inventory to freeze in S01:

1. Identical valid before/after output: no invented improvement or regression.
2. One wrong-but-schema-valid header/line value: the relevant loss is visible.
3. Correct-to-wrong change: regression cannot disappear inside an aggregate gain.
4. Missing row: its complete field penalties and row count remain.
5. Extra row: primary denominator/penalties remain; gold-only transitions cannot
   conceal the row regression.
6. Reordered/duplicated products: source-order scoring is not repaired.
7. Invalid/truncated/failed output with expected-null gold: zero rescued matches.
8. Terminal not-attempted case: remains selected, with no synthetic zero latency.
9. Missing or duplicate pairing member: no accepted selective comparison.
10. Changed source/record/label hash: provenance fails before analysis.
11. Non-permitted context/thinking/sampling/representation difference: no matched
    intervention claim; no alias or policy normalization introduced to hide it.
12. Unknown paid charge: total cost remains unavailable and known sum a lower bound.
13. Synthetic known-correct no-change case and unsupported proposal: unnecessary
    change and false support/acceptance are detected against explicit fixture
    truth, reported separately from human-reviewed domain judgments.
14. Unknown/unreviewed anchor: abstention/unavailable metrics, not claimed success.
15. Benign/instruction-injection and marker-disclosure pairs: controlled outputs
    cannot alter evaluation policy or acquire effects/authority; disclosure is
    recorded separately from task correctness and application enforcement.
16. Hostile valid strings and bounded oversized/failed-request pairs: preserve
    data semantics without execution; existing request/resource ceilings hold.

The suite's authority/error outcomes are fixed fixtures, not observed LLM attack
results. If a selected boundary does not exist in the current application,
record that capability as absent and do not fabricate an enforcement success.
Synthetic oracle review is a technical control check, not human factual approval
of a customer-derived label. Never combine synthetic controls with gold10 rates.

New model requests/tokens/API spend remain **0 / 0 / $0**. Offline verification
gets a 15-minute limit per command and P01-E01 analysis a 5-minute limit per
invocation; record failures on overrun, inspect the cause and revise the protocol
explicitly before a rerun. No automatic retry loop. Archive retrieval has bounded
existing transfer limits and does not authorize inference. No changes to the
existing cumulative spending cap, reservations or unresolved holds are needed.

## 7. Topic mapping and coverage limits

Use the source editions and coverage semantics pinned in
[roadmap section 4](../../roadmap.md#4-sources-and-meaning-of-topic-coverage):
AI Engineer topic revision `5a0a5314418aad4bded3ccdeea958e50d8386a5f`
and OWASP LLM Top 10 **2025**. This draft inherits that mapping; it does not
claim a fresh review of the external sources or completed topic coverage.

| AI Engineer topics | Slice / evidence |
| --- | --- |
| How LLMs Work; Tokens; Context Window; Inference | S06 explains inherited admission, token/output, reasoning, truncation and runtime evidence |
| Temperature; Top-P; Structured Output; Choosing the Right Model; Self-Hosted Models | S01/S06 preserve controlled factors and distinguish schema validity, task accuracy and deployment trade-offs; no new sweep |
| LLM Evaluations; Deterministic Evals; Evaluation Metrics; Regression Testing | S01–S07 protocol, independent controls, complete paired populations and reproduced reports |
| Human Evals | S02 review rubric/anchor provenance; new human evaluation is demonstrated only when actual reviewed judgments exist |
| Model-Based Evals | C01 only, with reviewed anchors, disagreement and false acceptance; unexercised by default |
| Prompt Injection Attacks; Conducting Adversarial Testing | S05 controlled benign/attack fixtures and boundary effects; real model attack susceptibility remains unmeasured |

| OWASP 2025 topic | Bounded P01 exercise / limit |
| --- | --- |
| LLM01 Prompt Injection | Document-instruction fixtures do not control evaluation/application policy; no real-model resistance claim |
| LLM02 Sensitive Information Disclosure | Synthetic cross-case markers, private exclusion and redacted errors; no real credentials and no blanket leakage guarantee |
| LLM05 Improper Output Handling | Hostile valid strings remain data through existing JSON/export boundaries; absent browser/spreadsheet consumers are deferred |
| LLM07 System Prompt Leakage | Harmless disclosure probes distinguish disclosure from authority; prompts contain no authorization secrets; live leakage unmeasured |
| LLM09 Misinformation | Wrong valid values, null inflation, unsupported acceptance, regression and incomplete populations receive independent checks; judge metrics conditional |
| LLM10 Unbounded Consumption | Reuse and check admission/retry/time/spend boundaries with controlled requests; analysis limits and zero inference remain explicit |

## 8. Completion, stop conditions and handoff

- [x] S01–S02 protocol, exposure inventory and rubrics are versioned with honest
  review status; no new documents/labels or independent holdout are assumed.
- [x] S03–S05 needed evaluation extensions and all selected controls work through
  actual application boundaries, with independent expected results.
- [x] S06 P01-E01 meets its finite-suite thresholds and explains its saved-data
  findings/fundamentals without claiming a fresh extraction improvement.
- [x] S07 full checks, historical/new reproduction, rejected altered evidence,
  privacy and archival checks pass; evidence and residual risks are recorded.
- [x] Roadmap/guide/report identify P01's decision and the next separately selected
  question. Conditional judge/live-model/security coverage remains unexercised
  unless separately selected, approved and actually measured.

Stop on changed frozen evidence, private exposure, unexpected network/model
work, accounting writes, unreviewed labels presented as truth or a comparison
that cannot meet its declared identity/population. Preserve the evidence and
resolve the cause; do not weaken checks or rerun inference to make the gate pass.

Rollback removes only P01's new code/metadata/outputs using the recorded source
checkpoint. Original runs, labels, ledger, archives and storage identities are
not migration targets and are never reset or rewritten. Git commit/publication
requires a separate request. The user explicitly requested execution on 2026-11-01. This plan alone grants
no inference or spending permission.

## 9. Revision history

| Version | Date | Change |
| --- | --- | --- |
| 1.0 | 2026-10-31 | Draft ordered offline-first P01 plan grounded in inherited evaluation, with paired reporting, exposure/review rules, bounded challenges and conditional judge work. |

## 10. Initial S01–S02 checkpoint — 2026-11-01

This initial checkpoint is superseded by the S03–S07 conclusion below.

S01 verified the pinned section 8 archive and selected bundles/terminal records.
Sixty saved native baseline records cover thirty cases per prompt, including
ten approved gold cases. Generation controls match after the existing public
manifest-bound administrative budget normalization; original execution policies
remain recorded. No new normalization or inference was introduced.

The exposure inventory records thirty cases and twenty-five transitive
source/layout groups. Uncertain example/inspection/review history stays unknown.
The S02 rubric defines error/review units without adding human judgments.
Protocol v1 retains the initial inventory freeze; v2 binds standalone controls
and rubric before implementation. Neither version is an execution permission.

S03–S07 remain pending. No new evaluation capability, control-suite pass, paired
result or P01 completion is claimed by these metadata files. No model calls,
ledger writes or Git publication occurred.

### S03–S07 conclusion — 2026-11-01

Implemented strict protocol/source binding, offline CLI/Make commands, paired
comparison, review-aware metrics, null/error categories, finite technical
challenges and model-fundamentals reference. Final isolated gate: 982 tests,
Ruff lint/format, strict mypy, gold validation and preflight passed. Historical
reproduction and byte-identical workspace/isolated paired reports passed. Real
CLI controls rejected altered results, protocol bindings and record payloads.

The control suite has sixteen declared groups mapped to fourteen test functions,
including parameterized cases and inherited controls. It is not sixteen new
LLM attack runs. No human semantic review or judge calibration was added.

Frozen declarations remain versioned: v1 inventory, v2 rubric/text controls,
v3 executable control binding, v4 final separate output (protocol format v3).
The initial analysis remains locally retained; the verified final proof was
archived, full-GET verified and restored exactly. See the
[execution report](../../reports/P01-evaluation-protocols.md) for counts, decisions
and limitations. C01 and P02 execution remain separate decisions.

| 1.1 | 2026-11-01 | Execute S01–S07 offline: strict protocols, paired reporting, bounded controls, exact reproduction and verified archival; judge study remains unselected. |
