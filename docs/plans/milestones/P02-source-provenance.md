# P02 — Inspectable field provenance and bounded source support

- Version: **1.0**.
- Created: **2026-11-07**.
- Status: **Draft; not approved for execution**.
- Parent: [P02 roadmap](../../roadmap.md#p02--spreadsheet-understanding-and-source-grounding).
- Planning baseline: `3be1bdd` — P01 and framework/SDK proposals committed.
- Selected question: **P02-E01, offline provenance verification**.

## 1. Outcome and selected boundary

Can an offline assessor attach verifiable source locations to selected saved
extraction fields, preserve ambiguity, and distinguish a literal occurrence
from evidence supporting the field's business meaning?

Deliver a separate, hash-bound provenance sidecar and reproducible report.
The first scope uses existing approved UTF-8 texts and saved native v2 baseline
outputs. It does not generate better extractions or certify a purchase order.
Exact source locations are the new capability; existing semantic checks remain
inherited, with their original scope and limitations.

P02-E01 requires **zero model calls, zero generated tokens and $0 additional API
spend**. No additional customer documents or new human labels are assumed.
Source-support accuracy on real cases is unavailable without reviewed support
anchors. Synthetic technical controls can establish finite behavior separately.

The broader P02 roadmap permits later workbook/representation experiments.
This plan selects only the text-provenance slice. Completing it concludes that
selected capability, not a general spreadsheet-understanding milestone.

## 2. Inherited capability and the actual addition

| Surface | Reuse | New responsibility |
| --- | --- | --- |
| Source integrity | Checked approved input bytes, source/rendered hashes and source-map validation | Exact UTF-8 byte ranges and quotations bound to those approved bytes |
| Row/cell parsing | `source_support/cells.py`, declared diagnostic layouts and recorded source references | Map existing cell/line references to original text locations without inventing workbook coordinates |
| Diagnostics | Row membership, completeness/quantity checks and identifier/date role checks | Attach location evidence without silently widening or replacing their rules |
| Evaluation | P01 exposure/rubric policy, archive verification, record loading and unchanged scorer | Provenance-specific protocol, controls and coverage/error reporting |
| Historical experiments | Representation, selection, scoped roles, correction, examples and header/line split reports | No repeated trial or claimed new accuracy gain |
| Preservation | Existing copy-only archive/restore and ledger-free reproduction | Retain a new derivation bundle and compact proof index |

Relevant implemented boundaries: [source support](../../guides/source-support.md),
[row diagnostics](../../guides/row-diagnostics.md),
[P01 handoff](../../reports/P01-evaluation-protocols.md#decision-and-handoff) and
[evaluation protocol guide](../../guides/evaluation-protocols.md).

P01's `EvaluationProtocol` currently requires named v1/v2 sides, all thirty
inputs and its own fixed control inventory. It is not a general protocol engine.
Reuse suitable binding/archive/serialization primitives; add a narrow P02
protocol rather than feeding this experiment through P01 by loosening its
checks. Historical P01 protocol files, commands and results remain unchanged.

## 3. Frozen population, fields and evidence contract

### Population and authority

- Select exactly the **thirty native v2 baseline records** already bound by
  P01-E01's v2 selection, retaining original run/record/source identities,
  failures and original model/prompt/runtime/settings. Use the pinned archived
  evidence, not a best-output or latest-run search.
- S01 freezes their explicit IDs and hashes before producing new results.
  Missing/duplicate records fail selection; a saved failed record remains a
  record-level unknown, not an omitted case or a fabricated extraction.
- Use all thirty for provenance coverage. Gold10 remains development data;
  the other twenty remain unlabeled. Reuse P01 exposure/source-layout groups.
- Detection and evidence binding read no gold answers or annotation content.
  Any optional unchanged gold-scoring reproduction remains a separate evaluator
  operation; it does not create source-support labels.

### Field scope

| Output path | Literal occurrence | Semantic support in this slice |
| --- | --- | --- |
| `/purchaseOrderNumber` | Locate exact non-null string occurrences in approved source text | Unknown in this slice; a match is an inspection candidate, not a new header-role inference |
| `/lineItems/*/buyerProductIdentifier` | Locate exact non-null occurrences; attach existing role-resolution cells/context where available | Reuse the existing identifier-role check without new labels, layouts or product matching rules |
| `/lineItems/*/buyerDeliveryDate` | Locate exact non-null occurrences; attach existing role-resolution cells/context where available | Reuse the existing line-date check; a normalized date without an exact occurrence does not justify a fabricated value span |

All other fields are outside the first declared field scope. They cannot be
claimed supported through a record-level summary. Ordered-row membership and
completeness retain separate existing diagnostics; supporting an identifier or
date does not establish that its output line belongs to the order.

### Sidecar semantics

Keep metadata outside PO v1 objects and historical run records. Bind each
sidecar to protocol/rule/implementation identity, input/source hash, original
manifest/record hash, extraction identity and the selected JSON path/value.

Use **zero-based, half-open UTF-8 byte offsets into the original approved input**.
The referenced slice must decode on complete character boundaries and equal
the retained quotation exactly. Preserve CRLF, Unicode and original literals;
do not normalize before indexing. Line numbers and already-present projected
sheet/cell references are optional display aids, not replacement coordinates.
No PDF page or original workbook position may be reconstructed by guessing.

Keep two independent dimensions:

1. **Location:** exact occurrence candidates, ambiguous candidates, no exact
   occurrence, null value or unusable extraction, with explicit reasons.
   A unique literal occurrence alone does not prove a semantic field role.
2. **Support:** supported/contradicted/unknown plus the inherited check and
   reason, evidence role and authority. Distinguish value, label, row/context
   and closed-scope/absence evidence. Failure to find an exact match does not
   establish contradiction.

Reviewed support anchors, if separately selected, are evaluator truth only;
they never supply the assessor's verdict or source location. Do not use a
review label as an apparent independent detection result.

Null does not have a literal value span. An inherited explicit-blank or
closed-scope absence resolution must retain its actual context/rule evidence;
never quote an arbitrary blank as proof of global absence. Unknown qualifiers,
unmatched/repeated products or an unaudited scope remain unknown under the
existing rules. Do not change an inherited verdict merely because location
resolution fails: retain it as inherited and mark the new linkage unresolved.
Only fully validated linkage may count as newly inspectable support evidence.

Repeated text keeps distinct candidate locations. Do not choose the first
match as the correct row. Reference validation must check source identity,
output identity/path and the intended cell/context, not merely a quote that
exists somewhere in the document. Any declared normalization used by inherited
rules retains raw evidence and its rule ID; normalized output is not a raw quote.

## 4. Ordered implementation slices

### P02-S01 — Freeze the experiment and reusable baseline

1. Inventory current diagnostics and decide which findings can carry exact
   source locations without changing their semantics. Record unsupported cases.
2. Restore/check the pinned evidence through the existing archive workflow.
   Freeze the thirty v2 record bindings, approved input hashes, three field
   patterns, rubric/exposure versions and original check identities.
3. Create a versioned P02-E01 protocol, control inventory and synthetic anchors.
   Freeze them before measuring saved-case results. An anchor records its
   technical or human-review authority explicitly; agent-authored fixtures do
   not acquire human-reviewed status.
4. Bind the location/support distinction, thresholds and resource ceilings below.
   Preserve earlier protocol revisions if a material change is needed.

**Accept S01:** exact input/record/field populations and expected controls are
frozen; inherited checks and new byte-location work are distinguishable. No
new data authority, inference permission or unseen-case claim is introduced.

### P02-S02 — Implement original-text locations and strict bindings

1. Add focused sidecar metadata and byte-span validation within `source_support`.
   Pydantic may validate this operational metadata, not a second PO model.
2. Locate exact field-value candidates and resolve existing source references
   using original source lines/cells. Retain ambiguous/overflow/unlocatable
   reasons and existing raw evidence instead of inventing a unique location.
3. Validate ranges, UTF-8 boundaries, quotes, source/record/path bindings and
   reference roles on construction and reload. A stale/tampered sidecar fails
   verification; it is not silently regenerated as a successful check.
4. Read only confined regular files. Reject paths escaping approved roots,
   symlink substitutions, unsupported versions and duplicate JSON keys using
   existing artifact utilities where applicable.

**Accept S02:** every emitted reference is reconstructible from pinned bytes;
each known-bad binding is rejected at its intended boundary. Positive Unicode,
CRLF and repeated-value cases work without source normalization or mutation.

### P02-S03 — Attach inherited support without widening its authority

1. Assess the same saved outputs with the existing identifier/date rules and
   attach value, label, product-row and scope references where resolvable.
2. Retain original status/reason/values, including supported nulls and unknowns.
   Keep diagnostic-only findings distinct from validated sidecar linkage.
3. For raw text not recognized by the inherited parser, provide occurrence
   candidates with semantic unknown. No new free-text role resolver, fuzzy
   matching, quantity rule, date parser or absence heuristic is selected here.
4. Verify before/after inherited findings on the same frozen records. Compare
   semantic payloads independently of added metadata; no existing result may
   change through this attachment-only intervention.

**Accept S03:** inherited diagnostic behavior is unchanged; every selected field
on each usable extraction has an explicit result, and unusable records remain
visible. New location success never upgrades semantic unknown or certifies a PO.

### P02-S04 — Add offline commands and separate evaluation populations

1. Add model-free protocol validation and assessment through the existing CLI
   and Make/Docker workflow. Proposed targets: `validate-provenance-protocol`
   and `assess-provenance`, with explicit protocol and restored evidence root.
2. Write a new ignored result directory containing the frozen protocol, sidecar,
   summary and checksums. Refuse replacement; provide `--check-result` to
   regenerate and compare without rewriting evidence. Redact operational errors.
3. Report record outcomes and selected-field counts; split literal-location,
   validated support-linkage and inherited semantic outcomes. Keep candidate
   occurrences distinct from field counts. Extra output rows remain selected.
4. Evaluate synthetic controls separately. Human-reviewed support precision,
   false support and missed contradictions use only applicable reviewed anchors;
   absent anchors produce unavailable rates, not zero errors. Report all unknowns
   and coverage denominators, including which failed records have no field paths.
5. Record elapsed assessment time, bound identities and zero new generation.
   Saved inference usage/timing is inherited and cannot be presented as new
   end-to-end measurement. Human review-time improvement remains unmeasured.

**Accept S04:** the real CLI preserves populations, refuses altered/missing
evidence and produces reproducible results without model/provider setup, gold
answer reads or accounting writes.

### P02-S05 — Verify, reproduce, archive and record the decision

1. Add focused behavior tests after implementation, with independently specified
   quotes, offsets, statuses and totals. Cover the control inventory below;
   do not calculate test oracles with the locator/checker under test.
2. Run relevant focused checks, then `make check` in Docker. Preserve historical
   matrix evaluation and P01-E01 report reproduction. Do not rerun inference.
3. Reproduce P02 from a public source export and pinned evidence without private
   settings/ledger/model runtimes. Reject altered result/source/sidecar controls
   through the actual CLI. Verify original inputs, records and frozen assets
   remain unchanged; evaluation must not initialize or write a ledger.
4. Archive detailed evidence with existing selection/upload/full-GET/restore
   checks. Version only the compact indices, code, protocol/controls and bounded
   report. Garage remains local recovery, not an off-device backup claim.
5. Document adopt/reject/defer outcomes separately for location mechanics,
   inherited support linkage and any semantic claims. Update roadmap, guide,
   report and relevant glossary evidence; do not mark conditional work complete.

**Accept S05:** finite gates below pass, exact reproduction/restoration succeeds,
and limitations are explicit. Failed mechanics cannot be closed merely by
rejecting the candidate; an honest negative semantic result can close its
research question without promoting the check into enforcement.

## 5. Thresholds, controls and limits

| Gate | Predeclared criterion |
| --- | --- |
| Population | Exactly 30 pinned records; zero silent omissions, duplicates or best-output substitutions |
| Field accounting | 100% of declared field paths on usable outputs represented; failed/unusable records separately retained; no unsupported fields counted as supported |
| Reference integrity | 100% of emitted references resolve to exact pinned byte slices; zero accepted stale, forged or cross-input/record/path bindings in controls |
| Behavioral preservation | Zero inherited verdict/reason/value changes on the fixed saved population; historical PO scores and P01 reports unchanged |
| Non-vacuous positive controls | At least one complete positive location case for each of the three field kinds and positive linkage cases for both inherited semantic checks; synthetic authority is explicit |
| Finite control suite | All 18 groups below have bound independent expected outcomes and passing positive/negative cases; zero observed false support or false contradiction on declared synthetic anchors |
| Real semantic validity | No minimum accuracy claim without reviewed anchors; unknown/unreviewed rates remain unavailable, with observed coverage reported |
| Reproduction/preservation | Byte-identical P02 payload reproduction, exact archive restoration, unchanged frozen/source evidence and no accounting writes |

The eighteen control groups cover:

1. Exact occurrence and independently hand-specified byte range.
2. Multibyte Unicode, combining characters and invalid mid-character boundaries.
3. LF/CRLF, empty lines and missing final newline without offset drift.
4. Negative, reversed, out-of-range and empty value spans; quote mismatch.
5. Changed source bytes/hash, including locally rechecksummed forged evidence.
6. Wrong input, record, output JSON path/value or unsupported sidecar version.
7. Repeated phrases and identical values in different rows/sheets.
8. A valid quotation attached to the wrong business role or source cell.
9. Leading-zero identifiers and substring-only matches that cannot grant support.
10. Normalized dates without an exact literal and ambiguous date representations.
11. Explicit blank, absent value, unknown scope and null output as distinct cases.
12. Legitimate buyer-owned code versus seller code and line date versus header date.
13. Duplicate/unmatched product descriptions and repeated output rows.
14. Unsupported/free-text sources, candidate overflow and unresolved inherited references.
15. Failed/truncated/not-attempted outputs and missing/duplicate saved records.
16. Changed protocol, control, result or sidecar binding through the real CLI.
17. Instruction-like/formula/URL/markup strings retained as data; no execution,
    external fetch or evaluation-policy change; confined-path/symlink negatives.
18. Real-process zero-model/gold-answer/accounting isolation, immutable originals,
    repeatable output and refused output replacement.

This suite establishes finite technical behavior, not live model attack
resistance or real-world semantic precision. Unsupported cases must abstain;
rejecting everything cannot satisfy the positive controls.

Resource ceilings: **0 model calls / 0 generated tokens / $0 new API spend**;
at most 30 saved records, 4 MiB source text per input, 10,000 output lines per
record, 64 occurrence candidates per field and 128 MiB serialized result payload.
Protocol validation and each verification command are capped at 900 seconds;
one assessment at 300 seconds. Source/record/output/deadline overruns fail with
an explicit resource error; candidate overflow retains a bounded candidate set
with overflow/ambiguous status, never a complete-search or unique-support claim.
Check limits before accumulating unbounded data. S01 verifies that the pinned
population fits; if not, revise the protocol with a recorded reason before
assessment, rather than excluding inconvenient cases. No automatic retry loop.

## 6. Affected areas and verification handoff

| Proposed area | Responsibility |
| --- | --- |
| `src/extraction_service/source_support/` | Cohesive span/sidecar metadata, exact location resolution and inherited-finding attachment |
| `src/extraction_service/evaluation/` | Narrow P02 protocol and provenance metrics; reuse existing integrity utilities without relaxing P01 |
| Existing CLI, Makefile and offline Docker service | Explicit offline validation/assessment/result-check entrypoints; no new runtime |
| `config/evaluation/` | P02-E01 protocol, field/check inventory and technical anchor metadata; frozen P01 files untouched |
| Existing source-support tests plus focused provenance tests | Independent reference/ambiguity/binding/CLI/population controls |
| `docs/guides/`, `docs/reports/`, glossary | Exact commands, measured findings, authority/limits and scoped completion status |
| Ignored `results/` and compact `archive-index/` | Full sidecars/proof bundles and verified restore references |

No new dependencies are selected. Propose a dependency separately only if the
bounded capability cannot use the current standard-library/project utilities.
Choose focused modules during implementation; this list does not require empty
packages, a general plugin framework or a second execution/evaluation harness.

The following commands are **proposed interfaces, not implemented commands**:

```sh
make validate-provenance-protocol ARGS='--protocol config/evaluation/P02-E01-v1.json --source results/restored/<pinned-archive>/submission'
make assess-provenance ARGS='--protocol config/evaluation/P02-E01-v1.json --source results/restored/<pinned-archive>/submission'
make assess-provenance ARGS='--protocol config/evaluation/P02-E01-v1.json --source results/restored/<pinned-archive>/submission --check-result results/submission/P02-E01-v1/report.json'
make check
```

S01/S04 replace the archive placeholder with the verified binding and publish
exact reproduction/archive commands in the operating guide. Human verification
inspects an unambiguous source link, a repeated-value ambiguity, a correct quote
with the wrong role and a null/absence case. Those UI-free inspection actions
do not create semantic review anchors unless the reviewer explicitly records
the source, judgment, scope and version through the separate anchor procedure.

## 7. Conditional work and milestone boundaries

| Extension | Selection requirement |
| --- | --- |
| Reviewed real-case support study | Explicit anchor procedure/population and numeric semantic adoption thresholds before evaluation; existing documents may be reviewed, with no new document collection assumed |
| New semantic resolver or enforcement | Named failure and separate protocol; false support/missed-error analysis first; no rejection/correction/routing enabled by this plan |
| Workbook parsing/representation | A separately selected P02 slice with supported formats, fixture authority, formula/cached-value/merged-cell semantics and coverage/completeness criteria |
| New model/prompt/cropping/chunking experiment | Separate matched intervention, full-workflow metrics and resource approval; no further Gemma tuning by default |
| Retrieval/embeddings/vector store | P03 |
| Tools, approval workflow, LangChain/LangGraph | P04 or its conditional framework comparison |
| LangSmith, API/UI and operational release loop | Conditional P04/P05 scope |

The topic sources/editions are those in
[roadmap section 4](../../roadmap.md#4-sources-and-meaning-of-topic-coverage).
No new external source review or framework adoption is claimed by this draft.

| AI Engineer topics | Selected exercise and limit |
| --- | --- |
| Input Format; Structured Output; Constraints | Separate validated sidecar, original-source identity and bounded selected fields; no new model output experiment |
| Context Sources; Context Evaluation; Context Failure Modes | Verifiable references, role/location distinction, ambiguity and unknown coverage |
| Manual Implementation; Deterministic Evals; Evaluation Metrics | Offline assessor, independently anchored controls and preserved populations; no agent/tool-calling claim |
| System Prompting; Zero-Shot; Few-Shot | Inherited experiments only; no new prompt/example work selected |

| OWASP 2025 risk | Bounded exercise and limit |
| --- | --- |
| LLM01 Prompt Injection | Instruction-like source strings cannot alter offline assessment policy; live model susceptibility unmeasured |
| LLM02 Sensitive Information Disclosure | Approved neutral evidence and private-material exclusions; no external requests or trace export |
| LLM03 Supply Chain | Source/record/protocol/rule identities and forged-reference rejection |
| LLM05 Improper Output Handling | Quotes and hostile values stay data; no workbook/browser executor introduced |
| LLM09 Misinformation | Separate occurrence, role support and correctness; no invented source locations or semantic review authority |
| LLM10 Unbounded Consumption | Explicit population, size, candidate, output and deadline limits with failed/unknown outcomes retained |

## 8. Completion, stop conditions and revision history

- [ ] S01 protocol, field/record population and independently authored controls frozen.
- [ ] S02 exact references and tamper rejection demonstrated without invented locations.
- [ ] S03 inherited semantic behavior preserved; unknowns and unresolved linkage explicit.
- [ ] S04 real offline entrypoints and separate populations verified with no inference/gold-answer/accounting side effects.
- [ ] S05 checks, original-evidence preservation, reproduction and archival completed.
- [ ] Selected text-provenance outcome and remaining P02 workbook/semantic-study decisions recorded honestly.

Stop on changed frozen evidence, private exposure, unexpected network/model
requests, accounting writes, altered inherited semantics or unreviewed judgments
presented as approved labels. Preserve partial evidence and identify the failed
gate. Missing archives require restore/access resolution, never fresh inference.

Rollback removes only P02 additions/new results using the recorded source
baseline. Original extraction records, gold/schema/prompts, P01 protocols,
archives and ledger remain unchanged. Drafting this plan authorizes no
implementation, Git operation, inference, installation or trace export.

| Version | Date | Change |
| --- | --- | --- |
| 1.0 | 2026-11-07 | Draft the zero-inference text-provenance slice: pinned native v2 population, three field kinds, exact source references, inherited support linkage, independent controls and conditional broader P02 work. |
