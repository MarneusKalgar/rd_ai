# Revised required provider/local matrix (7.2)

**Evidence availability — 25 October 2026:** the [compact review snapshot](../results/submission/v2-baseline-review-20261025/summary.json) and [availability index](../results/submission/v2-baseline-review-20261025/evidence-index.json) are included in this checkpoint. New v2 raw/preparation/detailed evaluation bundles referenced below are retained locally and intentionally unversioned pending archival. A fresh checkout cannot reproduce their saved-run evaluation yet. See the [checkpoint notes](../results/submission/v2-baseline-review-20261025/README.md).

## Current status — 24 October 2026

**Frozen v2 baseline phases complete and verified on 24 October 2026.** Native
Gemma attempted all30 with **29/30 schema-valid**, gold **7.16%**, 303 extra
gold rows and one exact gold document. Stronger Gemini Flash saved **30/30
schema-valid**, gold **100% (342/342)** and **10/10 exact gold documents**.
Gold10 is development data; the other20 have no gold labels. Both reuse their
saved gold10 exactly once with disjoint remaining20 continuations. See
[v2 continuation results](v2-continuation-results.md) for failures, checked exports,
matched comparisons, timings and budget evidence.

V2 remains frozen at SHA-256
`6a03379937695a2e5b127d292fc6ddb2301c9048b730ca3f9982d6c6443d155b`.
Native settings remain 49,152 context, 16,384 output and thinking=false; Flash
retains default reasoning and 16,384 output. The 732-test gate passed. Gemma
is unloaded. Provider v2 cost **$0.88064190**; cumulative accounted spend
**$3.52909660**, prior unknown holds **$0.50135040**, remaining **$6.47090340**.
Required coverage is **120/240**; four exploratory variants (**120 primaries**)
remain. Qwen3.5 9B is a separately planned optional gold10 comparison before a
Gemma-specific harness. **No further inference, model download or paid invocation
is approved.** Keep examples/skills and behavioral semantic correction separate.

## Execution update — 23 October 2026

**Review gate:** finish and verify the revised v1 baselines, then stop for the
user to review the results. Do not create, freeze or run v2, or run exploratory
sampling, before that review and further user direction.

**Provider v1 baseline complete and verified:** the approved continuation
`matrix-provider-v1-baseline-remaining-20261023-72` saved 20/20 valid outputs,
one call each, no retry/correction or dependency/budget stop. Combined with
`flash-v1-gold-16384-20261022`, it forms exactly 30 unique baseline inputs,
30/30 valid, gold **278/342 (81.29%)**, one exact document and no extra/missing
gold rows. The unchanged gold score is reused evidence, not a second gold run.

Across all30, p50/p95 input latency is **11.983 / 33.568 seconds** and known
API cost **$1.20499515** (saved gold10 $0.32986350 plus new20 $0.87513165).
All new charges settled; no new unknown holds. Cumulative accounted spend is
now **$2.64845470**, including unchanged prior holds of **$0.50135040**.
Remaining allowance is **$7.35154530**, including **$1.44871130** protected
matrix funds. These supersede the preparation balances below.

The continuation's separate evaluation bundle aggregates both source runs
with explicit audited-budget revision handling; all source hashes/policies
remain visible. It is saved under
`results/submission/matrix-provider-v1-baseline-remaining-20261023-72-evaluation/`.
The raw continuation is saved separately beside it; the original gold10 bundle
is unchanged. Native continuation is also complete and verified: 28/29 new
outputs valid; combined with saved S008, **29/30 valid**, gold **164/3,494
(4.69%)**, 394 extra gold line items and zero exact gold documents. S033
truncated at 16,384 output tokens. The model was unloaded and residency checked.
See [both revised v1 baselines](revised-v1-baseline-results.md) for the scoring
denominator, latency, source memberships and exports. Stop for user review;
no v2 or exploratory work and no additional paid invocation are approved.

The [audited budget revision](budget-revisions.md) and explicit budget-policy
aggregation compatibility are implemented. The full offline gate passed
**684 tests**, lint/format/types, gold validation and preflight. The real cap
raise to $10 preserved all 105 prior reservations, opening evidence, matrix
reserve and unknown holds; accounted spend remained $1.77332305.

The active revised entrypoint is **`config/matrix.yaml`**, retaining the original
configurations and uncommitted v2 work. It registers v1 only with both 16,384
sampling settings; no v2 is selected until baseline review. Native invocations
use `HW01_CONTEXT_LENGTH=49152` explicitly. Budget commands must use this
configuration to match the migrated ledger.

Fresh route/native metadata verifies the 11 reusable observations. An explicit
240-entry membership inventory and exact remaining-input schedules are retained
in `results/submission/matrix-revised-preparation-20261023/`. All 29 remaining
native initial requests passed render-only admission without generation probes.
Actual corrections still require separate admission.

Both terminal continuations retain unique run/configuration identities and
verified exports. The checked 240-entry inventory now records 60 covered v1
baseline observations and 180 unexecuted observations behind the user review
gate. No exploratory or v2 inference has started. The full 7.2 matrix is not
complete; only its revised v1 baseline phase is complete.

The design specification below records the rationale and implementation gates;
its earlier pending-migration descriptions are superseded by this update.

**Revised plan — 22 October 2026; in progress, authorized budget migration pending.** The user requested this revision after the v1 model/output/context diagnostics, then increased the experiment budget to **$10**, showing the OpenRouter lifetime limit. The target comparison remains all 30 approved inputs × two models × v1/v2 × two sampling settings: **240 primary observations**, including failures. The new target uses stronger Gemini 3.5 Flash and native Gemma with sufficient output capacity. This supersedes the original Flash-Lite/4,096 required-matrix profile prospectively; preserve the original complete baselines and every diagnostic unchanged. Updating the plan does not execute inference, change the live configuration/ledger, or approve a paid invocation.

## Evidence and target execution profiles

- Original full-corpus v1/baseline: Flash-Lite at 4,096 produced 25/30 valid and 40.15% gold field accuracy; native Gemma with thinking=false produced 21/30 valid and 17.24%. The earlier thinking-enabled Gemma run remains a separate diagnostic. These are budget-constrained historical baselines, not members of the revised matrix.
- Stronger Flash gold10 at 4,096 / 8,192 / 16,384 scored 33.52% / 59.94% / 81.29%; validity 8/10 / 9/10 / 10/10. At 16,384 there were no extra/missing lines and one exact document. S040 completed at only 6,260 actual tokens, so single-run reasoning variability prevents claiming a necessary 16,384-token threshold. Flash-Lite at 8,192 still overselected catalog rows; more output capacity alone is not a quality fix.
- Native S008 at 49,152 context / 16,384 output / thinking=false completed schema-valid JSON in 519.550 seconds, using 15,592 output tokens. It returned 207 rows, 194 with null quantities. S008 is unlabeled; no factual accuracy is claimed. The model was unloaded after verification. See [native large-context diagnostic](native-large-context.md).
- The committed v1 runtime/evidence is `e1ed2a3`; its isolated v1-only snapshot passed **672 tests**, lint/format, strict types, gold validation and preflight. The v2 prompt, registration, exploratory sampling and their fixture changes remain uncommitted. No v2 or exploratory inference has run. See [baseline review](matrix-baseline-review.md), [Flash diagnostics](stronger-model-experiment.md).

| Control | Revised provider target | Revised local target |
| --- | --- | --- |
| Model / evidence ID | `google/gemini-3.5-flash` / `provider-flash` | Pinned `gemma4:e4b-it-qat` / `local` |
| Deployment | OpenRouter, only `google-ai-studio`, no fallback/compression | Existing native desktop Ollama, no Docker Ollama |
| Output allowance | 16,384 including any provider reasoning | 16,384, explicit thinking=false |
| Context | Refresh provider route's advertised limit; accepted matrix admission policy | 49,152 effective loaded context, checked per actual request |
| Baseline sampling | `baseline-16384`: temperature 0, top_p 1 | Same ID and values |
| Second sampling | `exploratory-16384`: temperature 0.2, top_p 0.9 | Same ID and values |

Preserve v1 bytes, authoritative schema, approved corpus/gold, shared parsing/scoring and retry/correction/deadline policy. Apply the separately authorized $10 cumulative experiment ceiling only through the audited migration below; the runtime still enforces $4.50 until that work completes. Freeze the effective local runtime/digest/tokenizer/context/thinking profile across matched variants and record provider-reported identities/reasoning usage. Recheck the installed runtime before continuing; do not silently pool runtime updates. Explicit thinking controls differ between deployments and must be disclosed. A common allowance is not identical final-answer capacity or tokenization across models.

The main experiment configuration still contains the historical provider/output settings. Implement and verify the revised profile in a subsequent execution task; keep the existing standalone diagnostic configurations as original evidence. Retain a safe local default and exact sampling IDs needed for reuse. Preflight full inputs, schema, proposed v2 and prepared corrections against local context; admit each actual correction separately. Do not truncate inputs, silently enlarge context, or substitute a different model when admission fails. Native Gemma advertises 131,072 maximum context, but this plan selects 49,152, not the maximum.

## Reuse and remaining work

Declare an explicit membership manifest without rewriting any source run/configuration/hash. Reuse requires identical source/schema/v1 hashes, model/evidence ID, provider route or actual native runtime/digest/tokenizer, sampling controls, thinking/context and request execution controls. The explicit exception is the authorized budget-only revision from $4.50 to $10: source observations completed without budget stops, and the original caps must remain visible. Implement/test compatible aggregation for that revision before reuse; the current evaluator groups by the entire execution policy and would otherwise split the old/new caps into separate variants. Do not normalize changed deadlines, retries, context or thinking as a budget revision. Refreshing metadata must not silently merge incompatible observations. If a compatibility check fails, exclude the affected source observation from membership and rebaseline explicitly; do not select outputs by score.

| Revised matrix component | Reusable source | Remaining primary requests |
| --- | --- | ---: |
| Provider v1 / baseline-16384, all 30 | `flash-v1-gold-16384-20261022`, exactly gold10 | 20 non-gold inputs |
| Native v1 / baseline-16384, all 30 | `native-s008-49152-16384-20261022`, exactly S008 | 29 other inputs |
| Provider v1 / exploratory-16384 | None | 30 |
| Native v1 / exploratory-16384 | None | 30 |
| Provider v2 / both sampling settings | None | 60 |
| Native v2 / both sampling settings | None | 60 |
| **Total** | **11 existing observations, counted once** | **229: 110 provider + 119 local** |

The 11 reused observations were originally diagnostics and were excluded from the original matrix. This revision explicitly promotes only the compatible **16,384** provider gold10 and native S008 observations into the revised baseline. Retain their original diagnostic intent and gold-only/one-case populations in the history; do not relabel the raw manifests. All 4,096/8,192 outputs, Flash-Lite screening and native thinking-enabled observations remain outside revised membership.

## Authorized $10 budget migration and feasibility gate

The user increased the experiment budget to **$10** on 22 October, with an OpenRouter screenshot showing a $10 lifetime/key limit and rounded $1.27 spend. This authorizes the planned cumulative ceiling increase, not a paid inference invocation. The assignment originally allows up to $5 in API costs; report the user-authorized experiment extension explicitly rather than claiming the original assignment allowance itself changed. Record original and extended experiment spending in the final report.

The application configuration and persisted ledger still enforce **$4.50**. Both strict validators currently reject a $10 policy, and ledger reads reject a configuration/persisted-policy mismatch. Changing an OpenRouter dashboard limit alone does not alter either guard. Before further paid work, implement an explicit audited cap-raise operation and matching configuration validation; do not delete/reinitialize the ledger or simply change YAML and bypass the mismatch.

The cap-raise must acquire the ledger lock, validate the old cap/state, preserve every original reservation ID/key/stage/price/charge/resolution and opening-spend evidence, retain matrix_reserve_usd=3.5, record the user authorization and old/new caps, back up the prior bytes/hash, and persist atomically. Reject cap reductions, invalid/unapproved caps and missing/corrupt ledgers. Preserve read-only evaluation of historical $4.50 manifests and old exports. Test successful migration, unchanged accounted totals/holds, mismatched policy rejection and failure recovery without automatic reinitialization. The model/evidence migration and audited budget administration are implementation work, not part of this plan edit.

Current cumulative accounted spend is **$1.77332305**: known reported charges **$1.27197265** plus **$0.50135040** unresolved earlier Mistral holds. The screenshot's rounded $1.27 is consistent with known charges but is not itemized billing evidence sufficient to release holds. Reconcile unknowns only with exact billing evidence; do not assume zero or treat them as known charges.

| Budget quantity | Current enforced policy | Authorized policy after migration |
| --- | ---: | ---: |
| Cumulative cap | $4.50 | $10.00 |
| Accounted spend, including holds | $1.77332305 | Unchanged |
| Remaining conservative allowance | $2.72667695 | **$8.22667695** |
| Unspent protected matrix funds | $2.32384295 | Unchanged |

The latest verified Flash full-context reservation at 16,384 is **$1.720320 per physical call**; refresh route/context/prices before a new phase. After migration, headroom before another call's reservation stops fitting becomes **$6.50635695** of additional accounted spend, assuming that bound is unchanged. Unknown charges retain reservations and may still stop the run. Serial reservation sums are not expected bills.

The completed Flash gold10 cost $0.32986350. Linear scaling to the **110 remaining provider primaries** gives **$3.62849850**, excluding retries/corrections. Under the $10 cap this fits the remaining allowance at that observed average and leaves roughly $4.59817845 after those primaries, above one current reservation. This is a feasibility signal, not a guarantee or forecast: larger inputs, reasoning and v2/sampling may change cost. Prepare phase-specific usage estimates and preserve guards; consider trustworthy complete-request certificates only if verified and useful, not as an invented estimate to bypass reservations.

The budget increase changes the current evaluator's execution descriptor. Add an explicit compatible budget-revision path for the 11 reusable completed observations, retain every source cap and run hash, and regression-test aggregation into the intended variants without weakening duplicate detection or combining altered generation controls. A budget-stopped historical run must retain its stop and untouched outcomes rather than being presented as completed after a cap increase.

After audited policy/configuration/profile updates, aggregation compatibility, offline checks and refreshed pricing/context evidence, request separate approval of each exact paid invocation and allowance. No previous diagnostic approval permits another provider call. If actual feasibility deteriorates, report it and request an explicit scope decision; the 240-observation target is not silently reduced. Native work requires no API spend but is a separate execution task, not part of this plan edit.

## Baseline completion, prompt review and remaining variants

Both revised v1 baselines are complete and verified: the remaining20 provider
and remaining29 native observations were combined with the 11 compatible saved
observations, preserving failures and source hashes. Reuse these results rather
than rerunning v1 to begin v2. Review all30 per deployment: factual accuracy on
gold10, operations over all30. Truncation/invalid output remains a measured
failure; untouched inputs leave a future phase incomplete. See the
[revised v1 results](revised-v1-baseline-results.md).

After user review and further direction, review and freeze v2. A v2 draft already exists from the original baseline review; do not recreate it or claim it was written after the revised baselines. Its original unexecuted draft hash was `c2c6c61dcdd3fe9c93fcaf9b40d6f811a30fb9351e6918fcaa899459021e5ba0`; the 24 October frozen revision and results are recorded above. Reconcile its general ordered-row, buyer-identifier, line-date, address and unit rules against the revised baseline evidence. Record any subsequent edits, new hash, rationale and examples in the prompt changelog. No case-specific answer leakage or frozen schema/input/gold/scorer edits. All gold10 were used in model/profile selection and prompt development; report development-set scores, not held-out generalization.

Keep the initial v1/v2 comparison on the existing pipeline: strict JSON/schema
validation, the same correction policy and unchanged gold scoring. Semantic
checks may be designed and assessed against saved v1 outputs before v2, but must
not reject, filter, repair or trigger correction only for v2. Follow the separate
semantic-validation sequence in 7.3.2 below. Existing full-corpus v1 results do
not need rerunning merely to inspect or flag their source-evidence errors.

Both v2/baseline variants are complete. The remaining **120 primaries** are v1/v2 exploratory sampling on both models. The native gold10/remaining20 split changes execution order, not the all30 requirement or 240-observation target. Keep 16,384 output, the selected runtime/thinking/context, deadlines, retries and scoring matched across prompts. Freeze any profile change as a new explicit variant rather than changing only v2 or failed cases. Every paid invocation still needs approval and budget admission.

Finish section 8 from an explicit **240-observation membership inventory**, eight complete 30-input variants, duplicate rejection, checked exports and preserved source hashes. Report gold10 quality, all30 operations, reasoning/output usage, null/present correctness, row errors and known/unknown costs. Historical constrained-budget and Docker/runtime diagnostics receive separate tables. Docker Ollama's stopped container, image and weights volume were removed at the user's request; native weights/results remain. Docker runs Python/offline checks; native is the selected model runtime. Optional Docker compatibility code remains in source and must not download/start Ollama implicitly.

## Staged instruction-only v2 execution (7.2.5)

**Steps 1–5 baseline execution complete on 24 October 2026.** The user
approved both remaining20 continuations, which are verified with their reused
gold10. Preserve the original draft/history and the staged controls below.
Exploratory execution remains pending; see [terminal v2 results](v2-continuation-results.md).
No further invocation is authorized.

1. **Revise and freeze a shared instruction-only prompt.** Reconcile the draft
   against the revised v1 results and source-evidence observations. Clarify
   quantity-to-product linkage; scope blank-quantity exclusion to catalog/order
   entry evidence rather than globally dropping otherwise explicitly ordered
   items with unknown quantities. Retain conservative buyer-ID ownership,
   line-linked dates, source-order address components, decimal precision and
   unit rules. Include no synthetic worked examples, benchmark answer objects,
   skill content or new multi-stage model workflow in this initial v2.
   Both Gemma and stronger
   Flash must receive the same frozen instruction bytes and schema. Record the
   revision rationale/hash in the changelog; update the stale 4,096-token wording
   and register the reviewed revision in `config/matrix.yaml`. Do not use the
   older Flash-Lite/$4.50 configuration as the revised experiment profile.
2. **Verify the matched profile and request admission.** Preserve the latest
   v1 controls below. Recheck actual native runtime/model/tokenizer identities
   before reuse and admit the complete revised instructions, schema, source and
   output allowance. Actual corrections require their own admission. No silent
   input truncation, context increase, thinking change or output-limit change.
   A profile mismatch needs an explicitly separate variant or rebaseline.
3. **Run native Gemma on exactly the approved gold10 first.** When execution is
   separately requested after prompt review/freeze, use v2/baseline-16384 and
   matrix-stage records with a unique run ID and explicit input membership.
   Retain every attempted failure and untouched outcome. Report first/final
   validity, gold field/row/null errors, exact documents, total calls/tokens and
   latency against the saved matching v1 gold subset. Do not describe this
   10-input phase as a completed all30 baseline or as held-out evaluation.
4. **Stop for user review and approval before native remaining20.** No score
   threshold automatically approves continuation. If approved with unchanged
   prompt bytes and effective execution controls, run exactly the disjoint
   remaining20 and aggregate checked source runs into one 30-input variant.
   Preserve both run IDs/hashes; count each input once. These unlabeled20 add
   operational and qualitative evidence, not new factual accuracy labels.
   If gold10 observations motivate a prompt change, assign/freeze a new revision
   and hash, rerun gold10 under it, and only then complete its remaining20 after
   approval. Never pool earlier gold results with a changed prompt/profile.
5. **Provider v2 and exploratory variants remain separate phases.** Flash can
   use the same frozen v2; it is not a local-only prompt. Prepare current provider
   route/context/pricing evidence and a concrete command/allowance for approval
   before any paid invocation. Local continuation approval supplies no provider
   authorization. Complete the two v2 baseline variants before proceeding to
   the four all30 exploratory variants, subject to further direction and paid
   approvals. Preserve the full 240-observation membership target, including
   failures; extra revision trials remain separately identified diagnostics.

| Control | Native Gemma v2 | Provider Flash v2 |
| --- | --- | --- |
| Context | **49,152**, matching revised v1 | Existing verified provider-enforced policy; refresh evidence |
| Output allowance | **16,384** | **16,384**, including any reasoning usage |
| Thinking/reasoning | **thinking=false** | Preserve revised v1 default reasoning |
| Baseline sampling | **temperature 0, top_p 1** | Same |
| Pipeline | Existing JSON/schema validation and bounded correction | Same |

The recorded native model maximum is 131,072, but this comparison selects
49,152. Raising context beyond that only for v2 would confound the prompt
comparison. Keep deterministic semantic diagnostics detection-only; they must
not filter rows, reject output or trigger new correction calls in this matrix.

## Optional extraction skill experiment (7.3.1)

**Proposed after the v1 user review; documentation only.** The user requested
planning a reusable extraction skill that Gemma can actually consume. This does
not authorize skill implementation, v2 changes, inference, model downloads or
an autonomous agent loop. Keep this optional exercise separate from the required
240-observation prompt/sampling matrix.

The current Ollama adapter sends instructions, schema and source text through
`request_messages`; it has no skill discovery, resource loader or tool loop.
Placing a `SKILL.md` file in the repository alone would not affect inference.
A skill packages instructions/resources; it does not train or enlarge the model.

Reserve synthetic worked examples for this separate experiment and keep them
out of the initial v2 run. An invented example is a prompting technique, not
automatically answer leakage; disclose the design and any benchmark-informed
assumptions. Gold10 remains development data. Once the application loads an
example from the skill, it becomes model context and needs its own version/hash
and measured comparison. A file on disk supplies no model capability by itself.

### First approach: application-controlled loading

- Package concise extraction instructions in `SKILL.md`, with references to
  the authoritative contract, small worked examples and optional validation
  scripts. Focus on ordered versus catalog rows, explicit order evidence,
  quantities versus package sizes, buyer versus supplier identifiers, line-date
  linkage, null semantics and unit normalization. Derive rules from source
  evidence; do not impose a universal non-null-quantity filter that could remove
  legitimate order lines.
- Have the application explicitly load the selected instructions and relevant
  examples into the request. Gemma need not discover a skill or read files.
  Include the fully rendered request in context admission; preserve complete
  approved source/schema and retain the existing failure policy when it does
  not fit. Record package/resource hashes and loaded content in run evidence.
- First measure instruction/example loading alone as a separate prompt variant.
  With the same rendered instructions, skill packaging itself offers no new
  model capability; it provides reusable organization and versioning.
- If instruction-only results remain insufficient, separately test a fixed
  application workflow: **select ordered rows with source references → extract
  fields from selected rows → validate source support**. The application owns
  transitions and executes any scripts. Keep intermediate selections, references,
  raw replies and validation failures outside the authoritative PO object;
  version the intermediate contract. Do not silently delete unsupported rows
  or repair the final extraction to improve its score.

### Comparison and acceptance

Keep the same model digest, runtime, thinking, sampling and context/output
controls where feasible, and the frozen inputs, schema and evaluator. Identify
all changed controls. Assign distinct prompt/package/workflow identities rather
than overwriting v1 or silently treating a multi-call workflow as prompt-only v2.
Record any input transformation explicitly and report it as a separate variant.

Evaluate gold10 field accuracy, extra/missing rows, null/present correctness and
exact documents; report validity and total latency over all30 when running a
complete comparison. Count every selection/extraction/validation/correction
call, generated tokens and failure. Local API charges remain zero, but additional
passes consume machine time; do not claim zero total operating cost. Disclose
all examples used for development; gold10 is not held out, and examples must not
contain case-specific benchmark answers. Improvement requires measured quality
gains with an explicit latency/call-count trade-off, not just valid JSON or the
presence of a skill file.

When implementation is separately requested, verify actual loaded instructions,
resource hashes/context admission and controlled multi-step behavior with
offline fixtures before model calls. Reuse the existing parsing/scoring and
evidence infrastructure. Do not run inference merely to add this plan item.

Model-selected skill discovery, dynamic resource loading and tool calling remain
deferred. They require explicit application integration, verified model support
and separate evaluation of tool selection. Consider them only if the fixed
workflow demonstrates a concrete need for autonomy. See the
[Agent Skills integration guide](https://github.com/agentskills/agentskills/blob/main/docs/client-implementation/adding-skills-support.mdx).

## Semantic validation sequence (7.3.2)

**Detection-only implementation authorized on 24 October 2026.** The first
catalog-row candidate and saved-run CLI are implemented; see
[deterministic row diagnostics](row-diagnostics.md) for supported structures,
unknown outcomes and evidence. Implementation and regression hardening passed
the 732-test offline gate; 60 saved v1
observations were inspected without inference, retaining source/output hashes
and historical scores. Keep the compact diagnostic summary and reproduction
command versioned; the verbose regenerable report belongs under ignored
`results/diagnostics/`, with its hash retained as generated-artifact metadata.
The other proposed deterministic candidates remain future
work. Behavioral rejection/correction and inference
remain unexecuted and require a separate task. This does not lift the v2 review
gate or authorize the optional extraction skill implementation.
Semantic validation checks whether source evidence supports the extracted facts,
including whether an output row represents an order. It supplements JSON/schema
validation; schema descriptions alone do not perform these source comparisons.

1. **Before v2: review and assess candidate checks offline.** Use saved v1
   responses, approved source texts and the contract to identify evidence rules
   and counterexamples. A detection-only diagnostic needs no model calls or full
   v1 rerun. Store flags separately with check/version identity, source/output
   hashes and supporting evidence; preserve original statuses, extractions and
   scores. Assess both false positives and missed errors on reviewed cases.
   Gold10 remains development evidence; do not claim the other20 are labeled.
   Treat blank quantity as case-dependent evidence, not a universal instruction
   to reject every row with a null quantity. Do not feed new diagnostic flags
   into the required matrix's requests or correction policy.
2. **Initial v1/v2 comparison: change the prompt only.** After user review and
   further direction, freeze v2 and run the required matched variants using the
   current pipeline and the gold10-first staging in 7.2.5. Native remaining20
   require user review and approval. Load no skill or worked examples into this
   initial v2. Preserve the completed v1 baselines. Keep row selection,
   source preprocessing, runtime validation and correction behavior unchanged
   across prompts so the prompt effect can be interpreted.
3. **After that comparison: test behavioral semantic validation separately.**
   When explicitly requested, give semantic rejection, evidence-based correction
   or the skill's multi-step workflow its own versioned experiment identity,
   outside the 240-observation prompt-only matrix. Compare the same frozen prompt
   with and without that behavior, preserving other controls. Reuse compatible
   saved no-check baseline observations with explicit membership rather than
   automatically rerunning all v1. New corrected outputs require actual measured
   calls; they cannot be inferred from detection flags. Bound all additional
   attempts, retain raw failures/intermediate evidence, and report total calls,
   tokens, latency and known/unknown costs alongside gold quality and check
   precision/recall on cases with reviewed check labels. No silent row deletion,
   output repair or rescoring of historical results. Each paid invocation still
   requires concrete approval and budget admission.

This sequence adds semantic-check design to the baseline review without making
new runtime validation a prerequisite for the prompt experiment. The extraction
skill proposal in 7.3.1 can reuse the assessed checks later; packaging them as a
skill does not change their experimental identity or prove their reliability.


## Optional Qwen3.5 9B comparison (7.3.3)

**Planned diagnostic; not executed.** Before investing in a Gemma-specific
skill or behavioral validation harness, compare a second local model family:
**`qwen3.5:9b-q4_K_M`**, through the existing native Ollama desktop runtime.
This plan edit authorizes no download, implementation or inference invocation.
Native Gemma remaining20, provider v2 and exploratory runs keep their existing
review/approval gates.

### Question and comparison boundary

Test whether changing the local model materially improves ordered-row selection
with the existing extraction pipeline. Reuse the verified Gemma v2 gold10 as
the comparator; do not rerun Gemma automatically. Qwen is a separate optional
model diagnostic, not a replacement for the selected Gemma baseline or a new
member of the required 240-observation matrix. Qwen observations do not increase required matrix coverage; see the latest
status and checked membership above for completed required phases.

The [exact Qwen artifact](https://ollama.com/library/qwen3.5:9b-q4_K_M)
is listed at approximately 6.6GB, versus approximately 6.1GB for the
[Gemma QAT artifact](https://ollama.com/library/gemma4:e4b-it-qat).
These are download sizes, not runtime memory requirements or equivalent compute
budgets. Gemma's E4B designation means effective parameters; Qwen 9B is not a
parameter-matched model. Describe this as a comparison within a similar weight
storage budget, and measure memory and speed rather than assuming equivalence.

### Preparation and matched controls

1. When execution is separately requested, verify the exact tag, digest,
   quantization, native runtime compatibility, tokenizer/template identity,
   structured-output support and whether thinking can actually be disabled.
   Keep Gemma's saved identities unchanged. Add an explicit diagnostic
   configuration/model identity; preserve ordinary defaults and Gemma records.
2. Use the same ten frozen gold inputs, v2 instruction bytes (SHA-256
   `6a03379937695a2e5b127d292fc6ddb2301c9048b730ca3f9982d6c6443d155b`),
   authoritative schema, input representation and gold scorer. Keep context
   **49,152**, output allowance **16,384**, temperature **0**, top_p **1**,
   and **thinking=false**, subject to verified support. Preserve deadlines,
   bounded retry/correction policy and sequential execution. No examples,
   skill resources, source filtering or behavioral semantic correction.
3. Audit and record the complete effective generation options, including
   artifact defaults such as presence/repetition penalties and top_k. Explicitly
   align supported controls where possible; disclose unavoidable model-specific
   behavior. Do not call the comparison perfectly controlled merely because
   temperature and top_p match. A thinking/profile mismatch requires a separately
   identified variant and review before inference, not a silent fallback.
4. Verify complete-request admission using Qwen's own tokenizer/template; do
   not reuse Gemma token counts or certificates. Check memory headroom on the
   16GiB M2 Pro with only one model resident. Keep the full input and schema;
   a failed admission or memory gate stops preparation rather than silently
   shrinking context/input/output. If the current admission path cannot verify
   Qwen, implement and test that support before generation; do not bypass it.
   Run Python/offline verification in Docker; model inference remains native.

### Execution, evidence and review gate

After a separate execution request and successful preparation, run exactly the
same gold10 once under a unique Qwen diagnostic run ID. Retain every outcome,
raw response, correction/retry and request/profile hash. No paid inference is
part of this diagnostic. Unload the model after completion and verify residency.

Report overall/header/line-field accuracy, exact documents, extra/missing rows,
first/final validity, truncations, calls, actual token usage, processing and
load times, model residency/GPU placement and observed memory. Inspect S016,
S032 and S040 explicitly, but keep all ten cases in the evaluation. Run the
existing source-row diagnostic only post hoc; it must not alter model outputs,
corrections or gold scores. Preserve checked raw exports and compact comparison
summaries; keep verbose regenerable row diagnostics ignored with a recorded hash.

A substantial reduction in unsupported catalog rows would support model choice
as a useful intervention; similar failures would strengthen the case for testing
input representation or staged row selection. One development-set comparison
cannot prove reliability, a universal small-model limit or harness effectiveness.
Stop for user review after gold10. Do not automatically run Qwen remaining20,
switch the selected local model, revise v2 or implement the harness. Any later
model substitution needs an explicit plan/membership update and matched matrix
coverage; this diagnostic does not silently satisfy Gemma's outstanding phases.

## Historical original 4,096-token phase

The following preparation notes, commands, prices and balances describe the
original profile. They are retained as history; the revised target and current
budget gate above supersede their forward-looking instructions.

### Provider context and spending

On 22 October 2026 the user accepted extending provider-enforced context to the
**matrix stage**. Each coverage document must explicitly include
`server_context_stages: ["matrix"]`, and the invocation still requires
`--allow-server-context`. Historical smoke/screening coverage does not authorize
matrix execution. The repetition stage remains excluded.

Retain full source and schema, disabled compression and route fallback, the
standard/default service tier, and an explicitly unverified complete-request
token count. Refresh exact endpoint capabilities, context and pricing before
execution. Reserve the full advertised context plus the output allowance and
applicable fees before every physical call. Settle to reported actual cost;
unknown charges retain their reservations. The policy acceptance does not
approve a paid invocation or attest that an individual request fits.

The existing cumulative ledger must be reopened, not reinitialized. Before this
phase it accounts for **$0.59716600**, including **$0.50135040** held for unknown
Mistral error charges. **$3.50** is protected for matrix work; the remaining total
budget is **$3.90283400**. Matrix calls may consume that reserve and reduce its
remaining amount. The runner enforces the existing $4.50 cumulative budget,
below the assignment's $5 cap. Each paid phase requires separate approval of
its exact command and allowance; no automatic continuation is authorized.

### Readiness and evidence

Preparation checks public provider metadata and native `/api/version`,
`/api/tags` and `/api/ps` without generation. Actual local composition checks
version compatibility, weights, installed tokenizer, loaded context and
CPU/GPU placement; each request then passes complete rendered-request admission.
Model loading/setup is recorded separately from input latency. Stop Docker
Ollama before native execution to avoid competing resident model memory.

Use unique run IDs for provider and local phases, preserve incremental attempts
and all terminal outcomes, then export and verify each run independently in a
fresh offline container. Save process logs, metadata/pricing evidence, ledger
summaries and offline evaluation with checksums. Track curated submission
bundles in Git; keep credentials, working logs and the mutable ledger ignored.

**Initial baselines are complete; the user-approved thinking-disabled local rebaseline is running.** The offline gate passed **659 tests**,
Ruff lint/format, strict mypy, all 10 gold validations and 30-input preflight.
Six new controlled regressions verify full-corpus matrix scheduling, gold-only
accuracy, prior-spend preservation, matrix-reserve accounting and stage/opt-in
rejection. Both initial native/provider baseline invocations completed all 30 inputs.
The user separately approved the concrete provider command and initial
$3.90283400 remaining cumulative allowance on 22 October. The user accepted explicit local thinking=false and a new 30-input native
baseline; no v2 or later phase has started.

#### Metadata preparation — 22 October 2026

At 14:43 UTC, metadata-only preparation confirmed native Ollama **0.40.7** and
model digest `ee665637121887cf3befff38abbb1be4ee117c7db867d97a67e29049ecd7e15f`.
The installed weights occupy 6,146,501,801 bytes. No Docker Ollama service was
started. Native setup/loading and effective placement will be checked by the
actual runner before extraction, separately from document timing.

At 14:44 UTC, the public exact-route catalog confirmed Gemini 3.5 Flash-Lite /
`google-ai-studio`, required parameters, route status 0, 1,048,576 context tokens
and a 65,536-token advertised output maximum. The experiment retains its
4,096-token output allowance. Standard text rates are $0.30/million input and
$2.50/million output, including internal reasoning where advertised; no fixed
request fee. No paid search, image/audio input, tools or plugins are enabled.
Every physical call reserves **$0.32481280** before settling reported cost.
The verified metadata/coverage is retained under
`results/setup/matrix-v1-baseline-20261022/` and
`results/provider-matrix-coverage-20261022.json`. The resolved baseline
configuration SHA-256 is
`bb5f59390d79095e195f589f026415577a56222b20873f472e02b868966981ee`.

The provider's 30 primaries would reserve $9.744384 if none settled before the
next call; the 120-call configured maximum has an unconstrained reservation
ceiling of $38.977536. These are **not expected bills**. Serial settlement and
the existing $3.90283400 remaining cumulative allowance constrain execution;
unknown charges retain their reservation and can cause an early stop. The
10-case screening cost $0.04512240 for this model, but scaling it to the full
corpus is only a rough indication because document sizes and failures differ.

#### Phase-one schedule and commands

The offline plan selects exactly 60 primaries / at most 240 physical calls across
the two models. Each separate model invocation selects 30 / at most 120.
There are no gold-only filters and no v2 or alternate-sampling jobs.

Native inference authorized by the 7.2 implementation request uses the desktop
server, through this command from the repository root:

```sh
make hw01-run MODE=native ARGS='--stage matrix --model local --prompt v1 --sampling baseline --run-id matrix-native-v1-baseline-20261022-72'
```

The user separately approved this exact provider command and allowance before execution:

```sh
make hw01-run MODE=provider ARGS='--stage matrix --model provider --prompt v1 --sampling baseline --coverage results/provider-matrix-coverage-20261022.json --allow-server-context --allow-provider --run-id matrix-provider-v1-baseline-20261022-72'
```

The provider invocation may use the existing remaining $3.90283400 cumulative
allowance, including the matrix reserve; unknown Mistral charges remain held.
No additional phase is scheduled by either command. Both use the same frozen
baseline configuration. Run IDs are unique evidence identities, not replay
commands. After execution, record approval/status/outcomes below before any
continuation.

#### Provider v1/baseline — completed

The separately approved provider run started at **14:51:56 UTC** on 22 October.
All 30 inputs were attempted once: **25 schema-valid outputs, five truncations,
zero untouched inputs**, no corrections/retries and no budget/dependency stop.
The manifest is `complete`; application exit 1 (Make error 2) accurately reports
failed extractions and does not mean the corpus run was interrupted.

Truncated inputs: S005, S014, S016, S019 and S040. Each retains the partial raw
response and `finish_reason: length`, with 4,079–4,080 reported output tokens.
No output allowance was increased and no partial JSON was repaired.

The 10 gold cases scored **163/406 = 40.15%** primary field accuracy, with
**0/10 exact documents**. Header matches were 51/70 and ordered-line matches
112/336. Extra rows add 64 wrong comparisons to the 342 expected gold field
units. This differs slightly from the earlier screening's 164/406 despite the
same controls; deterministic sampling settings do not establish byte-identical
provider outputs across separate requests.

Across all 30 inputs: validity **83.33%**, p50 **2.614 s**, p95 **9.588 s**,
30 physical calls and no unknown charges. Reported cost was **$0.15360260**;
all call reservations settled. Cumulative accounted spend is **$0.75076860**,
including unchanged historical unknown-charge holds of **$0.50135040**.
Remaining total allowance is **$3.74923140**; the unspent protected matrix
amount is **$3.34639740**. These are ledger amounts, not a claim that the
unknown historical charges were billed.

The [provider run bundle](../results/submission/matrix-provider-v1-baseline-20261022-72/)
contains all 30 records/checkpoints and hashes; its records revalidated in a
fresh offline container. The separate
[evaluation bundle](../results/submission/matrix-provider-v1-baseline-20261022-72-evaluation/)
contains the unchanged shared evaluator output and verified accounting summary.
Process/plan logs, configuration snapshot, evaluation and summary with checksums
are retained in `results/matrix-runs/matrix-provider-v1-baseline-20261022-72/`.
The native baseline subsequently completed; see its review and profile decision below.

The running native baseline's saved setup confirms a 32,768-token context,
Ollama 0.40.7 and GPU-resident memory (`size_vram` equals reported loaded
`size`: 3,234,773,072 bytes). This is the runtime's placement evidence, not
a claim that every operation is GPU-only. Initial loading took 17.467 seconds,
recorded separately from per-input durations. The tokenizer SHA-256 is
`42e3a238e10726346e996c7e3569fcfb2e8d47173944a3cd56826d8dc4d9a9fb`.

#### Native v1/baseline — completed diagnostic, thinking enabled

`matrix-native-v1-baseline-20261022-72` completed all 30 inputs: **19 valid,
11 truncated, zero untouched**, 30 physical requests, no correction/retry and no
dependency/budget stop. Its gold score is **89/406 = 21.92%**, exact documents
0/10, p50/p95 60.325/158.297 seconds. Model setup/loading is separate. Native
API cost is zero; cumulative provider accounting is unchanged at $0.75076860.
Both baseline exports and evaluations are retained and independently verified.

The [baseline review](matrix-baseline-review.md) found thinking enabled in all
30 raw responses. Six inputs consumed all 4,096 tokens in thinking before
emitting any answer; the installed `/api/show` metadata confirms default=true
and supports false. The user accepted disabling thinking and rerunning only the
native baseline before v2; the new run is recorded below. The completed provider
baseline stays reusable. V2 and the remaining 180 required requests have not
started. The model residency expired during the review pause and was reloaded
for the newly authorized run. Preserve this completed thinking-enabled diagnostic.

#### Thinking-disabled native rebaseline — authorized and started

The user accepted explicit thinking=false and a fresh 30-input native
v1/baseline, then renewed the instruction to continue after pausing before
execution. No generation occurred during that pause. The offline gate passed
**672 tests**, Ruff lint/format, strict mypy, gold validation and corpus preflight.
Both historical baseline exports still revalidate under the new optional fields.

The new run is `matrix-native-v1-baseline-nothink-20261022-72`:

```sh
make hw01-run MODE=native ARGS='--stage matrix --model local --prompt v1 --sampling baseline --run-id matrix-native-v1-baseline-nothink-20261022-72'
```

The only intended execution-profile change is explicit local thinking=false.
The same desktop Ollama runtime, model digest, 32,768 context, frozen v1/schema/
inputs, baseline sampling, 4,096 output allowance and execution/budget policy
remain. The configuration SHA-256 is
`b6d38d16fc8b6e0bf0f3f17bf449f604604bf6caf00200245d2d4ff1fc089a0f`.
Render-only admission, initial generation and any correction all send the same
thinking control. Setup/admission evidence records it; the request fingerprint
binds it. Aggregation separates differing thinking profiles.

The original thinking-enabled native run is retained as a separate diagnostic,
not a duplicate required matrix observation. The completed provider baseline is
reused unchanged. No extra provider call is included in this rebaseline. The
new local baseline must complete and be reviewed before v2 is created. Its raw
response envelopes will be checked for absent/empty thinking fields, rather than
assuming the requested control was honored.
