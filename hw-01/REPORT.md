# Purchase-order extraction: consolidated results

Verified 27 October 2026 from saved records, without new inference.

**Gemini 3.5 Flash with frozen v2 and baseline sampling is the strongest measured
complete-PO configuration on this corpus.** It matched all 342 approved gold
fields and all ten gold documents, completed all thirty inputs, and cost
$0.88064190 in reported API charges. Native Gemma needs source-aware assistance
and review: its best tested assisted pipeline matched 309/366 fields (84.43%)
but only two complete gold documents. Neither result establishes reliability on
unseen documents. The ten labeled documents were repeatedly used in development.

## Population, controls and scoring

The historical matrix contains **240 attempted input/variant observations**:
two models × two frozen prompts × two sampling settings × thirty inputs.
All eight variants cover the same thirty approved neutral documents exactly
once. Factual scoring uses the same **ten approved gold documents** per variant
(80 labeled observations); the other twenty have no factual accuracy labels.
Screening and optional diagnostics are separate populations. Reused gold or
largest-document observations count once in a matrix variant, not as new runs.

| Control | Matrix profile |
| --- | --- |
| Native model | `gemma4:e4b-it-qat`, Q4_0; Ollama 0.40.7; digest `ee665637121887cf3befff38abbb1be4ee117c7db867d97a67e29049ecd7e15f` |
| Native execution | Apple M2 Pro, 16 GiB unified memory; native Ollama reached by Python in Docker; 49,152 context; thinking=false; recorded processor `gpu_or_mixed` |
| Provider | `google/gemini-3.5-flash`, OpenRouter through `google-ai-studio`; default reasoning retained; no route fallback/compression |
| Provider admission | Provider-enforced context, advertised 1,048,576; local token capacity unverified, not a local token certificate |
| Baseline / exploratory | Temperature 0 / top_p 1; temperature 0.2 / top_p 0.9 |
| Output allowance | 16,384 tokens per physical call; output capacity is distinct from context capacity |
| Failure policy | 1,800s request and 7,205s input bounds; at most one transport retry and one schema correction, dependency/budget guards retained |
| Frozen artifacts | [v1](prompts/v1.txt), [v2](prompts/v2.txt), [authoritative schema](schemas/purchase-order-extraction.v1.schema.json); original hashes retained in the evaluation |

The [shared scorer](docs/reference/evaluation.md) validates the complete output,
then compares exact contract values and positional line fields. It performs no
sorting, deduplication, string normalization or partial-JSON rescue. Repeated
products remain separate ordered lines. Each gold document contributes seven
header fields plus eight fields per expected/predicted position, using the
larger line count. Each extra row adds eight wrong comparisons. A missing row
loses eight matches; row shifts can also lose later positional matches. Invalid,
truncated or unattempted outputs receive zero gold matches, including nulls.

Gold10 contains 34 ordered lines and **342 expected fields: 197 present and
145 null**. Present/null subsets cover expected fields only; extra-row penalties
are included in the overall/line denominator. Counts, row errors and exact
documents must accompany percentages. In particular, Gemma v2 exploratory has
a higher percentage than baseline while matching one fewer field.

## Provider screening and subsequent selection

The original screening used unchanged v1, temperature 0/top_p 1 and **4,096**
output tokens on gold10. These constrained-budget results are not matrix rows.

| Candidate | Attempted | First/final valid | Gold fields | Exact docs | p50 / p95 seconds | Known API cost |
| --- | ---: | ---: | --- | ---: | --- | ---: |
| Gemini 3.1 Flash-Lite | 10 | 7/7 | 141/406 = 34.73% | 0 | 1.704 / 17.884 | $0.03551070 |
| Gemini 3.5 Flash-Lite | 10 | 8/8 | 164/406 = 40.39% | 0 | 1.583 / 10.324 | $0.04512240 |
| Mistral Small 4 (`mistralai/mistral-small-2603`) | 3 per invocation, two invocations | 0/0; seven untouched per invocation | Unranked: upstream HTTP 429 | Unranked | Failed-request timings do not measure generation | Unknown |

The user accepted finishing screening with the Gemini pair. 3.5 Flash-Lite won
that comparison with better validity and field agreement, at higher measured
cost. Mistral remained unavailable; no conclusion about its extraction quality
follows. Twelve failed physical requests across its two invocations retain
$0.50135040 in unknown-charge holds.

Subsequent explicitly approved diagnostics exercised stronger **3.5 Flash** and
larger output allowances. Stronger Flash at 16,384 improved the v1 gold result
to 278/342 with all ten valid. This motivated the matrix provider selection;
it does not retroactively change the original screening winner. Output/reasoning
capacity, model and later prompt changes are separate interventions.
See [screening evidence](docs/reports/provider-screening-results.md) and
[model/output diagnostics](docs/reports/stronger-model-experiment.md).

## Complete matrix: quality on gold10

`B` means baseline 0/1; `E` means exploratory 0.2/0.9. Validity counts in the
next table use all30; quality counts here use gold10 only. `G` is native Gemma;
`F` is provider Flash. No failed input has been removed from the score.

| Variant | Gold fields | Accuracy | Exact / 10 | Headers | Ordered lines | Present / 197 | Null / 145 | Extra / missing gold rows |
| --- | --- | ---: | ---: | --- | --- | ---: | ---: | --- |
| G v1 B | 164/3494 | 4.69% | 0 | 61/70 | 103/3424 | 88 | 76 | 394 / 0 |
| G v1 E | 105/2542 | 4.13% | 0 | 55/70 | 50/2472 | 73 | 32 | 275 / 13 |
| G v2 B | 198/2766 | 7.16% | 1 | 68/70 | 130/2696 | 103 | 95 | 303 / 0 |
| G v2 E | 197/2214 | 8.90% | 1 | 67/70 | 130/2144 | 103 | 94 | 234 / 0 |
| F v1 B | 278/342 | 81.29% | 1 | 66/70 | 212/272 | 193 | 85 | 0 / 0 |
| F v1 E | 267/342 | 78.07% | 1 | 66/70 | 201/272 | 193 | 74 | 0 / 0 |
| F v2 B | 342/342 | 100.00% | 10 | 70/70 | 272/272 | 197 | 145 | 0 / 0 |
| F v2 E | 342/342 | 100.00% | 10 | 70/70 | 272/272 | 197 | 145 | 0 / 0 |

### Per-field matches / comparisons

Line denominators include extra-row penalties and retain missing/failed cases.
Every column has ten gold documents. `line.*` denotes `lineItems/*/`.

| Field | G v1 B | G v1 E | G v2 B | G v2 E | F v1 B | F v1 E | F v2 B | F v2 E |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| purchaseOrderNumber | 6/10 | 5/10 | 8/10 | 8/10 | 10/10 | 10/10 | 10/10 | 10/10 |
| purchaseOrderDateTime | 10/10 | 9/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 |
| buyerName | 10/10 | 9/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 |
| shipToInfo | 6/10 | 6/10 | 10/10 | 10/10 | 6/10 | 6/10 | 10/10 | 10/10 |
| paymentTerms | 10/10 | 9/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 |
| buyerCurrency | 9/10 | 8/10 | 10/10 | 9/10 | 10/10 | 10/10 | 10/10 | 10/10 |
| totalValue | 10/10 | 9/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 | 10/10 |
| line.purchaseOrderLineNumber | 17/428 | 4/309 | 33/337 | 33/268 | 34/34 | 23/34 | 34/34 | 34/34 |
| line.buyerProductIdentifier | 1/428 | 1/309 | 1/337 | 1/268 | 1/34 | 1/34 | 34/34 | 34/34 |
| line.buyerProductName | 4/428 | 4/309 | 7/337 | 7/268 | 34/34 | 34/34 | 34/34 | 34/34 |
| line.buyerProductQuantity | 4/428 | 4/309 | 8/337 | 8/268 | 34/34 | 34/34 | 34/34 | 34/34 |
| line.buyerProductUOM | 34/428 | 21/309 | 34/337 | 34/268 | 34/34 | 34/34 | 34/34 | 34/34 |
| line.quantityUnit | 3/428 | 3/309 | 7/337 | 7/268 | 34/34 | 34/34 | 34/34 | 34/34 |
| line.buyerUnitPrice | 22/428 | 9/309 | 22/337 | 22/268 | 34/34 | 34/34 | 34/34 | 34/34 |
| line.buyerDeliveryDate | 18/428 | 4/309 | 18/337 | 18/268 | 7/34 | 7/34 | 34/34 | 34/34 |

## Operations, time and cost on all30

All variants attempted thirty inputs in thirty physical requests, with **zero
transport retries, schema corrections, untouched inputs or unknown-cost calls**.
First and final valid counts are equal. Latency includes per-input admission,
request and coordinator work, including failures and any retries/corrections;
setup/build work is excluded. Percentiles use nearest rank over thirty samples.
Summed input durations combine reused and new observations; they are not wall
time for one uninterrupted batch or an isolated hardware benchmark.

| Variant | First/final valid / 30 | p50 / p95 seconds | Sum seconds | Reported API cost | API cost / 1,000 attempted docs |
| --- | --- | --- | ---: | ---: | ---: |
| G v1 B | 29/29 | 21.791 / 519.550 | 3475.918 | $0 | $0 |
| G v1 E | 28/28 | 21.729 / 500.241 | 3482.988 | $0 | $0 |
| G v2 B | 29/29 | 18.807 / 368.810 | 2591.917 | $0 | $0 |
| G v2 E | 30/30 | 20.148 / 225.909 | 1611.798 | $0 | $0 |
| F v1 B | 30/30 | 11.983 / 33.568 | 460.563 | $1.20499515 | $40.166505 |
| F v1 E | 30/30 | 15.427 / 33.449 | 520.264 | $1.20104190 | $40.034730 |
| F v2 B | 30/30 | 8.379 / 22.966 | 309.870 | $0.88064190 | $29.354730 |
| F v2 E | 30/30 | 9.320 / 29.297 | 356.964 | $0.90389520 | $30.129840 |

Retained truncations at 16,384 output tokens: G v1 B **S033**; G v1 E
**S004, S032**; G v2 B **S004**. S032 is labeled and loses its full gold field
population in G v1 E. The other failures are unlabeled and affect operations,
not gold accuracy. Complete membership includes these failed outcomes.

### Reported token usage

All matrix attempts report input and output counts. Provider output counts
include billable reasoning usage; native thinking is disabled. These are
provider/runtime measurements, not a shared tokenizer or equal-reasoning test.
The raw responses retain reasoning details where supplied; no missing reasoning
breakdown is inferred to be zero. Actual reported charges drive the cost table.

| Variant | Input tokens | Output tokens |
| --- | ---: | ---: |
| G v1 B | 155052 | 116007 |
| G v1 E | 155052 | 120795 |
| G v2 B | 172662 | 84046 |
| G v2 E | 172662 | 49616 |
| F v1 B | 154692 | 108234 |
| F v1 E | 154692 | 108013 |
| F v2 B | 172302 | 69382 |
| F v2 E | 172302 | 72356 |

Cost per 1,000 scales measured charges by attempted documents, including failed
attempts; it is not a quote for a different volume/document mix. Local API cost
is zero; hardware amortization, electricity, host contention and human review
costs were not measured. The four provider matrix variants total $4.19057415.
Across all paid experiments the ledger accounts for **$5.63403370**, consisting
of **$5.13268330 known charges plus $0.50135040 unresolved holds**. Remaining
allowance is $4.36596630 under the $10 cap. Reservations are not billed costs;
the old holds are neither attributed to this matrix nor silently released.

## Characteristic errors: expected versus actual

These examples come from approved neutral artifacts, not original private
workbooks. Paths are zero-based. Exact values and source run IDs are retained
in the consolidated evidence; they illustrate different failure modes.

| Case and run | Expected | Actual | Interpretation |
| --- | --- | --- | --- |
| S016, Gemma v2 baseline, `/lineItems` | 1 ordered row | 67 rows | Catalog inclusion dominates the line denominator despite valid JSON |
| S002, Flash v1 baseline, `/lineItems/0/buyerProductIdentifier` | `null` | `"XB1558"` | A visible generic code is not automatically a buyer-specific identifier |
| S003, Flash v1 baseline, `/shipToInfo` | `"Alderwick Stores Ltd; 17 Alder Lane"` | `"Alderwick Stores Ltd, 17 Alder Lane"` | Exact representation rule counts this mismatch; it is not evidence of an incorrect street |
| S032, Gemma v1 exploratory | Complete contract-valid PO | Truncated at 16,384 tokens; no final extraction | Partial JSON receives no rescued field matches |

Flash v2 matches the gold objects exactly, including nulls and ordered lines.
The independent recomputation checks record/checkpoint/schema/input hashes
before scoring. Agreement is with the approved labels under the declared
contract; it does not validate every source interpretation independently or
score the unlabeled twenty. The repeated development use makes a 100% result
an observation to preserve and audit, not a generalization certificate.

## Separate diagnostics and local assistance

These trials are not additional matrix cells. Unless stated otherwise they use
the same gold10 and therefore provide development evidence only.

| Trial | Measured result | Decision / limitation |
| --- | --- | --- |
| Flash v1 output 4,096 → 8,192 → 16,384 | 120/358 → 205/342 → 278/342; valid 8 → 9 → 10 | More output capacity helped this profile; default reasoning/usage varied; not proof 16,384 is always necessary |
| Flash-Lite v1 output 4,096 → 8,192 (separate diagnostic) | 163/406 → 170/934; valid 8 → 9 | More capacity did not resolve row selection; do not substitute its separate 4,096 run for screening |
| Gemma largest S008, 32,768/4,096 → 49,152/16,384 context/output | Truncated at 182.903s → valid at 519.550s, 207 rows | Unlabeled: 13 positive-quantity and 194 null-quantity rows; completeness is not factual correctness |
| Gemma thinking enabled vs disabled | Earlier default-thinking all30 had 11 truncations; disabled profile rebaselined | Distinct control profiles, not pooled in matrix |
| Qwen3.5 9B Q4_K_M, v1/v2, gold10 each | 103/406 (25.37%) / 112/366 (30.60%); 8 valid each; 0/1 exact; ~26m33s / 26m19s | Fewer matched fields than Gemma; 24 missing rows each and long-document truncations; no demonstrated replacement |
| Gemma sampling sweep, v2 gold10 | .2/1: 198/2614; .5/1: 193/2366; .2/.95: 192/2958; .2/.9: 197/2214; .5/.9: 132/2366 | Percentage changes do not establish robust improvement; .2/.9 gold reused once in matrix |

Qwen used explicit presence/frequency penalties 0, repeat penalty 1, top_k 40,
thinking=false, context 49,152 and output 16,384. It ran on Ollama 0.40.7 with
digest `56671c2ab9385f9cfcb404638e32cd62d88e3501d44822208363c010179a3c90`.
This comparison concerns the tested quantization/profile, not all Qwen/Gemma
models. See [Qwen details](docs/reports/qwen-gold-comparison.md) and
[sampling details](docs/reports/native-sampling-experiment.md).

### Gemma workflow trials: gold10, frozen v2

All use native API charges of zero. Processing seconds below are summed
retry-inclusive input durations; the correction row reconstructs baseline time
plus nine new correction calls. Source views and extra calls change the workflow,
so the table does not isolate model capability or prompt effects.

| Workflow | Gold fields | Exact / 10 | Extra / missing rows | Processing seconds |
| --- | --- | ---: | --- | ---: |
| Raw-source baseline | 198/2766 = 7.16% | 1 | 303 / 0 | 840.110 |
| Cell records | 144/2910 = 4.95% | 1 | 321 / 13 | 1213.651 |
| Ordered selection + cell fallback | 277/1214 = 22.82% | 1 | 109 / 0 | 289.866 |
| Ordered selection + exact raw fallback | 282/366 = 77.05% | 1 | 3 / 0 | 113.227 |
| Unscoped field-role cues | 295/1230 = 23.98% | 1 | 111 / 0 | 300.982 |
| Scoped field-role cues | 295/366 = 80.60% | 1 | 3 / 0 | 116.670 |
| Scoped cues + guarded buyer-ID correction | 309/366 = 84.43% | 2 | 3 / 0 | 269.382 |
| Scoped cues + synthetic examples | 296/390 = 75.90% | 2 | 6 / 0 | 129.885 |
| Scoped cues + independent header/line stages | 278/366 = 75.96% | 1 | 3 / 1 | 148.013 |

Selection/cues delivered the largest gains. Source-aware correction accepted
two whole candidates, rejected two off-target changes and left five unresolved;
these gains include source-derived assistance, not independently learned facts.
The app-loaded example package regressed from the scoped baseline and was not
adopted. Splitting headers/lines improved headers to 69/70 but worsened lines
to 209/296; its better headers cannot be combined with earlier line predictions
and reported as a measured pipeline. It used twenty primary calls and twice
the per-document output allowance. It was not adopted.

### Historical Docker/native evidence

The Docker CPU readiness check used six one-token initial/correction probes,
Ollama 0.40.6 and 32,768 context, reaching its 10 GiB container ceiling without
OOM. It took 733.949s for context diagnostics plus 61.538s model load; these
are not complete extraction timings or accuracy tests.

| v1 smoke input, 4,096 output | Earlier Docker CPU seconds | Native 0.40.3 seconds | Native outcome |
| --- | ---: | ---: | --- |
| S030 | 117.836 | 26.283 | Valid |
| S026 | 442.022 | 70.116 | Valid |
| S008 | See retained Docker smoke evidence; no matched complete output | 169.006 | Truncated |

Version, GPU placement, caches and actual output lengths were not isolated.
Do not attribute these differences solely to Docker overhead or combine these
samples with native 0.40.7 matrix latency. Docker Ollama resources were removed;
Python/offline checks still run in Docker. See
[runtime verification](docs/reports/native-runtime-verification.md) and
[CPU readiness context](docs/reports/local-runtime-comparison.md).

## Decision and remaining uncertainty

For a deployment candidate on this document mix, prefer **Flash v2 baseline**
with the frozen contract, full input, recorded route/settings, budget/dependency
guards, retained raw evidence and human escalation. It has the best measured
whole-document result, lower observed latency and lower reported cost than
Flash v1. Exploratory sampling provided no gold benefit and slightly higher
measured v2 time/cost. This is a candidate choice, not approval for unattended
production. Validation checks structure; it cannot certify factual correctness.

Use the tested Gemma profile for drafts or tightly constrained components with
source checks/review, rather than complete unattended extraction. Its header
performance is much stronger than line selection, but split execution did not
produce a reliable complete pipeline. Its zero API bill must be weighed against
hardware, processing and correction/review time. No general claim about the
limits of all small local models or unpublished Flash parameter counts follows.

The main limitations are ten repeatedly reused development labels, layout/source
overlap, benchmark-informed v2/examples/checks, strict representation scoring,
unlabeled remaining20, one observation per matrix cell/input, runtime/cache
variation, different reasoning profiles and historical rather than guaranteed
future route/pricing. No new documents are assumed available. Further reviewed
labels from the existing twenty could support a separately versioned evaluation,
provided the rules are frozen first and reuse is disclosed; provider predictions
alone must not become gold. Existing evidence can still support this report and
section 9 without inventing an independent test set.

Revisit the choice for independently reviewed errors, material cost/latency
changes, a different document/layout mix, or a local workflow with measured
whole-document reliability and lower total cost. **Unexecuted/deferred:** JEV
verification/routing, broader semantic correction, source cropping/chunking,
pruned stage prompts, more examples/general prompt tuning, fine-tuning, new
local models and independent evaluation. None is silently counted as completed
or authorized for inference by this report.

## Reproduction and retained evidence

The section 8 bundle contains the offline collection driver, all eight full
shared-evaluator variants, compact summaries, exact error values and the
240-entry membership. The driver validates every referenced source bundle,
record/checkpoint identity and membership hash, rejects duplicates, checks
the exact model/prompt/sampling Cartesian population, and calls the existing
scorer. Original budget policies remain visible under the audited $4.50→$10
administrative revision; reviewed sampling aliases change grouping names only.
It neither generates model requests nor changes records, gold or the ledger.

Use the [archive workflow](docs/guides/archiving-results.md) and the
`section8-consolidated` selection for the compact archive index and retrieval
commands. Restored reproduction must match `evaluation.json`, `summary.json`
and `errors.json` exactly. The historical section 8 driver used the local
audited ledger and cap-revision backup; neither private accounting file was
uploaded. Section 9 adds [ledger-free reproduction](docs/guides/reproducing-results.md)
through a public manifest-bound evaluation policy and the shared scorer.
`make hw01-reproduce-report` checks the published matrix and tables from the
indexed archive without model credentials, a private ledger or archived-code
execution. The source reports linked in the
[documentation index](docs/README.md) retain separate experiment protocols,
test gates and archive receipts. Bulk evidence stays ignored; reports, compact
indices, receipts and restore verification are versioned. Garage and local
caches remain on the same machine and do not constitute off-device backup.

Section 8 reused the **927-test** implementation gate and added saved-data
recomputation without new inference. Section 9 passed **938 tests**, Ruff
lint/format, strict mypy, frozen gold validation and preflight in an isolated
tracked-source export with the explicit candidate patch. The same export
reproduced the matrix using only its supplied public archive, without private
environment files, a ledger or a preexisting restore. This used the existing
Docker engine/cache, not a newly provisioned machine; no new inference ran.
