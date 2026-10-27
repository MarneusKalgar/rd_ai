# Bounded buyer identifier correction: Gemma gold10

## Scope and controls

The user authorized committing scoped-cue work and proceeding with the next
planned exercise. Commit `6dfee70` preserves that starting point. This replay
reuses its ten saved primary outputs; it generates no new primaries. The required
240-observation matrix and six preceding comparator runs remain unchanged.

`buyer-id-single-correction-v1` selects only source-contradicted buyer identifier
paths from the existing role checker. Unknown evidence abstains. A flagged input
receives at most one physical native correction request, with no transport retry,
schema retry or second semantic attempt. The baseline configuration's historical
retry setting is preserved as provenance but is not used by this phase.

The request contains the full unchanged source representation, frozen v2
instructions plus a versioned correction suffix, the starting complete PO and
source-derived role resolutions. Gold values and annotations do not participate
in generation or acceptance. Exact gold10 membership metadata limits scope.

The model must return a complete schema-valid object. Every targeted identifier
must resolve and every other field/row must remain unchanged. Legitimate buyer
codes, leading zeroes, dates, quantities, names, prices and row order are
protected. A comparison mask detects other changes; it never constructs a
merged extraction. Invalid, unresolved or off-target candidates retain the
starting output for review. All candidates and failures remain in evidence.

Controls match the saved scoped run: native Gemma4 e4b-it-qat, runtime 0.40.7,
unchanged digest/tokenizer, thinking=false, temperature 0/top_p 1, 49,152 context,
16,384 output allowance, authoritative schema and frozen v2/source representation.
There is no provider/JEV/remaining20/other-field correction in this exercise.
Python, verification and archiving run in Docker; inference uses native Ollama.

## Verification

The full offline gate passed 887 tests, Ruff lint/format, strict mypy, frozen gold
validation and preflight. Thirty-two new tests cover guard success and rejection,
supported/unknown identifiers, legitimate codes and leading zeroes, multiple
targets, invalid/truncated/refused responses, one-call/no-retry bounds, admission
and deadlines, provider/Docker exclusion, saved-run replay/export/CLI verification,
gold-independent generation, evaluation populations and evidence tampering.
Passing tests do not establish complete correctness or unseen-document reliability.

Non-generating preparation admitted 9 eligible requests with minimum context headroom of 24,315 tokens after the output allowance. Each actual request was separately admitted and its intent checkpointed before dispatch.

## Measured results

Gold scoring is unchanged. The retained pipeline includes all ten documents,
including starting outputs kept after rejection or no-call decisions. Counts
include extra-row penalties; this is not a score of accepted corrections only.

| Output population | Valid / 10 | Matched fields | Accuracy | Exact docs | Extra / missing rows |
| --- | ---: | --- | ---: | ---: | --- |
| Saved scoped primary | 10 | 295/366 | 80.60% | 1 | 3 / 0 |
| Retained after one correction phase | 10 | 309/366 | 84.43% | 2 | 3 / 0 |

Reused primary requests: **10**. New physical correction requests: **9**. New primaries: **0**.

| Decision | Documents |
| --- | ---: |
| `rejected_off_target_changes` | 2 |
| `rejected_unresolved_identifiers` | 5 |
| `guarded_correction_applied` | 2 |
| `no_identifier_contradiction` | 1 |

| Input | Targets | Decision | Before → retained matches | New calls | Correction seconds |
| --- | ---: | --- | --- | ---: | ---: |
| B02-S002-PO01 | 1 | `rejected_off_target_changes` | 12/15 → 12/15 | 1 | 16.35 |
| B02-S003-PO01 | 4 | `rejected_unresolved_identifiers` | 10/39 → 10/39 | 1 | 15.13 |
| B02-S012-PO01 | 1 | `rejected_unresolved_identifiers` | 13/15 → 13/15 | 1 | 7.85 |
| B02-S016-PO01 | 1 | `guarded_correction_applied` | 12/15 → 13/15 | 1 | 9.13 |
| B02-S021-PO01 | 0 | `no_identifier_contradiction` | 15/15 → 15/15 | 0 | 0.00 |
| B02-S032-PO01 | 13 | `guarded_correction_applied` | 98/111 → 111/111 | 1 | 33.52 |
| B02-S040-PO01 | 11 | `rejected_unresolved_identifiers` | 84/95 → 84/95 | 1 | 32.18 |
| B02-S044-PO01 | 3 | `rejected_off_target_changes` | 24/31 → 24/31 | 1 | 22.86 |
| B02-S011-PO01 | 1 | `rejected_unresolved_identifiers` | 13/15 → 13/15 | 1 | 7.23 |
| B02-S023-PO01 | 1 | `rejected_unresolved_identifiers` | 14/15 → 14/15 | 1 | 8.47 |

Actual candidates that changed protected fields were rejected in full:

- B02-S002-PO01: `/lineItems/0/quantityUnit`.

- B02-S044-PO01: `/lineItems/0/buyerProductUOM`, `/lineItems/1/buyerProductUOM`, `/lineItems/2/buyerProductUOM`.

Retained identifier-role findings: `{"contradicted": 22, "supported": 15}`. These assess field roles, not order membership or whole-PO correctness.

| Output population | Expected-present buyer IDs | Expected-null buyer IDs |
| --- | --- | --- |
| Saved scoped primary | 1/1 | 0/33 |
| Retained pipeline | 1/1 | 14/33 |

## Time and interpretation

Saved primary processing: **116.67s**.
New correction processing: **152.71s**.
Their sum is **269.38s**, a reconstructed
pipeline total, **not measured live end-to-end latency**. The correction phase
wall time was **163.93s**, including setup.
Hardware state and caches can affect these observational timings.

This exercise tests a source-guided pipeline, not independent learning of code
ownership by Gemma. The deterministic checker supplies source-role resolutions;
any improvement must be attributed accordingly. Whole-object retention prevents
silently combining the best fields from different candidates. Retained for
review does not mean semantically accepted or certified correct.

Gold10 was used to develop these conventions and choose interventions. This is
one development-set replay, not a held-out reliability or stability estimate.
Remaining errors in order membership, quantities, units, dates or other fields
require separate evidence and review. Stop here before another experiment.

Native API cost was zero, excluding hardware, electricity and human time. The
provider ledger stayed byte-for-byte unchanged, prior run payloads stayed unchanged
and native residency was empty after unloading.

## Retained evidence

- [Archive index](../../archive-index/e43e35b1f4704e80ed36982c938efee4b3e4964460a90aa94d6280f3777874ad.json).
- [Garage upload/full GET receipt](../../archive-index/e43e35b1f4704e80ed36982c938efee4b3e4964460a90aa94d6280f3777874ad.remote.json).
- [Restore and re-evaluation verification](../../archive-index/e43e35b1f4704e80ed36982c938efee4b3e4964460a90aa94d6280f3777874ad.verification.json).

Selection `identifier-correction` retains the preceding controls plus every
actual correction request/response, candidate, decision, original/retained
output, source/admission bindings, configuration, implementation/test snapshots,
drivers and execution/full-check logs. All restored bytes matched; correction
evaluation and all six comparator evaluations reproduced exactly. Required
matrix membership remains 240/240. Verbose evidence stays ignored by Git.
Garage and its cache remain on this laptop.
