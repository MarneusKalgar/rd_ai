# P01 — Evaluation protocol execution

Executed 2026-11-01 against source baseline `50d4e4d` plus the explicit P01
candidate. The first next question is answered with offline comparison/control
verification, not new extraction inference. P01-C01 judge calibration remains
unselected. No new human factual labels, provider/native calls or ledger writes
were needed.

## Implemented capability and provenance

- Frozen exposure inventory: thirty inputs, ten approved development-gold cases,
  twenty unlabeled cases and twenty-five transitive source/layout groups. Unknown
  prompt-example exposure, individual inspection and additional review remain
  unknown; no input is declared an independent holdout.
- Protocol revisions retain the initial inventory freeze (v1), rubric/control
  text bindings (v2), executable control inventory (v3), and final separate output
  selection (v4, protocol format v3). The first analysis is preserved. Population,
  control thresholds and the zero-inference policy did not change after results.
- Exact selected archive, run manifest, record, corpus, gold, schema, exposure,
  rubric, control and public budget-policy identities are bound. Original
  execution policies stay visible. Only the existing manifest-bound $4.50/$10
  administrative budget normalization applies; runtime/context/thinking/sampling/
  output/representation differences are not normalized away.
- The two sides contain sixty saved records: thirty per prompt, same native
  Gemma4 runtime/digest, 49,152 context, thinking=false, temperature 0/top_p 1,
  16,384 output allowance and matching generation controls. Different collection
  times remain historical confounding; this is not randomized causal evidence.
- New commands validate protocols and compare checked saved runs offline. They
  enforce deadlines, redact errors, reject changed/overlapping/incomplete
  membership, preserve failed outcomes, refuse output replacement and can
  compare a saved report to regenerated evidence without rewriting it.

## Saved-data result

The primary scorer is unchanged. Gold-only transitions and overlapping error
tags are additional views, with separate populations and no semantic row repair.

| Gold10 measure | Native v1 | Native v2 |
| --- | ---: | ---: |
| Matched/compared fields | 164/3494 | 198/2766 |
| Primary accuracy | 4.69% | 7.16% |
| Header fields | 61/70 | 68/70 |
| Line fields, including extra rows | 103/3424 | 130/2696 |
| Exact documents | 0/10 | 1/10 |
| Extra / missing rows | 394 / 0 | 303 / 0 |
| Expected-present matches | 88/197 | 103/197 |
| Expected-null matches | 76/145 | 95/145 |

On **342 fixed gold field paths**: 152 both correct, 132 both wrong,
**46 wrong-to-correct**, **12 correct-to-wrong**. Extra rows remain penalized
in primary scores and reported separately, rather than counted as gold paths.
The primary gain is approximately **2.465 percentage points**, with 91 fewer
extra rows and 34 net additional gold-field matches. It does not erase the twelve
regressions or establish reliable complete extraction.

All thirty inputs per side were attempted: thirty physical requests and 29/30
final valid outputs on each side. Retry-inclusive p50/p95 were approximately
21.79s/519.55s for v1 and 18.81s/368.81s for v2. These are inherited timings;
P01 generated no new tokens. New human semantic review anchors are absent, so
false-acceptance rates remain unavailable rather than reported as zero errors.

## Verification

| Gate | Observed outcome |
| --- | --- |
| Implementation gate | Isolated-source `make check`: **982 tests passed in 306.89s**, Ruff lint/format, strict mypy on 212 source files, frozen gold validation and offline preflight |
| New behavioral controls | 26 focused cases, including protocol membership/control conflicts, changed bindings, exact transitions, extra rows, failed/null outputs, positive no-change, false support/acceptance, unknown anchors, hostile strings and CLI redaction/isolation |
| Sixteen declared control groups | Bound selector inventory maps the finite controls to new/inherited passing behavioral tests; includes failure/unknown-cost populations and admission/deadline controls. This is not sixteen live model attacks or a new security benchmark. |
| Historical reproduction | Same 240 observations, eight variants, 84 bundles and 1,594 payload files; evaluation and report tables match without private accounting |
| New analysis reproduction | Workspace and isolated-source final reports are byte-identical, including implementation/protocol hashes |
| Positive CLI control | Existing final result matches regenerated analysis without rewriting it |
| Changed-result negative | Altered accuracy delta rejected by the real CLI, exit 2 |
| Changed-protocol negative | Altered exposure hash rejected by the real CLI, exit 2 |
| Changed-record negative | Payload-byte mutation rejected at bundle checksum verification; real CLI exit 2 |

The isolated export includes public tracked/candidate files and the explicitly
supplied archive. It has no private settings, original results, ledger/backups,
private workbooks or model runtime. It reuses this host's Docker engine/cache;
it is not a newly provisioned machine or off-device disaster-recovery test.

## Security, authority and coverage limits

Controlled instruction/marker strings are retained as data and scored as wrong
when they differ from expected fields. A simulated marker disclosure may be
observed while application evaluation authority remains unaffected. This does
not establish real model resistance, secrecy or cross-case isolation under a
live attack. No browser, spreadsheet executor or tool-writing authority was
added solely to claim protection at an absent consumer boundary.

Synthetic review anchors are separate technical oracles. They do not become
human-approved customer labels. Source support, correctness and permission to
apply an edit remain distinct. A valid PO can be wrong; a refusal/invalid output
is not successful abstention. Review rate denominators stay explicit and empty
human populations remain unavailable. No unreviewed semantic cause is inferred
from positional mismatches.

P01's AI Engineer/OWASP mappings are qualified in the
[implementation plan](../plans/milestones/P01-evaluation-protocols.md#7-topic-mapping-and-coverage-limits).
Deterministic controls, metadata/rubric capability and saved-observation
fundamentals are demonstrated in their stated scope. New human evaluation,
model-based judging and live prompt-injection/leakage susceptibility remain
unexercised. Existing runtime/accounting/admission controls are inherited.

## Decision and handoff

Adopt the offline protocol/comparison capability. Preserve the model findings
as development evidence, including negative outcomes and regressions. Do not
run another Gemma, Qwen, provider, sampling or judge sweep automatically.

The next useful P02 question is whether explicit text-span provenance can make
source-support judgments inspectable and distinguish supported, contradicted
and unknown fields on existing representations. Define that experiment's
anchors, thresholds and scope first; P01 does not select an automatic semantic
correction/routing policy or assume new customer documents exist.

See the [operating guide](../guides/evaluation-protocols.md) and
[saved-observation fundamentals](../reference/model-fundamentals.md). Detailed
reports/logs belong in ignored archived evidence; public archive references and
final preservation outcomes are recorded below after archival verification.

## Archived proof and preservation

- [Public archive index](../../archive-index/1a8f9185c01fe7f5366d76ed35e7879384642859c117f40a090a75e3e376c9a0.json).
- [Garage full-download receipt](../../archive-index/1a8f9185c01fe7f5366d76ed35e7879384642859c117f40a090a75e3e376c9a0.remote.json).
- [Exact isolated-restore receipt](../../archive-index/1a8f9185c01fe7f5366d76ed35e7879384642859c117f40a090a75e3e376c9a0.verification.json).

All 535 payload files in 14 bundles matched originals
after isolated restoration. The public proof includes the final analysis,
frozen protocol/exposure/rubric/control metadata, implementation inventory,
passing gate/reproduction logs and intended negative controls. Its membership
copies the historical matrix solely to bind inherited source evidence; it
does not claim P01 executed 240 new observations.

The original spending ledger matches the pre-P01/S08 checkpoint byte-for-byte.
Frozen input/gold/schema/prompt and all prior archive-index bytes are unchanged.
Private inventories, settings and recovery copies are excluded from the public
proof. The first upload failed because Garage was stopped; starting the existing
service and retrying succeeded without initialization or credential changes.
Garage, the repository and temporary restores are on the same laptop, so this
is verified local recovery, not an off-device backup.

P01-S01–S07 are concluded for this scope. No source-data relabeling, inference,
paid spend, automatic commit or later milestone execution occurred.
