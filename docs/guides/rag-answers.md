# E03 matched RAG answers

Status on 2026-11-10: **S07 generation is complete** across 40 questions and
three arms: 108 physical calls, 107 schema/citation-valid answers, one preserved
provider-error response and 12 deterministic skips. Total E03 cost is
**$1.1270655**. Semantic review/replay and archival remain S08/S09 work. See the
[full generation report](../reports/P03-rag-answers.md),
[pilot history](../reports/P03-rag-pilot.md) and
[P03 plan](../plans/milestones/P03-authorized-retrieval.md#p03-s07--e03--llm-generated-cited-answers).

## Preparation checkpoint, before inference

- Full Docker gate: **1,118 passed, two optional SDK tests skipped**; Ruff,
  strict mypy, frozen gold validation and preflight passed.
- Final focused gate with the frozen manifest present: **46 passed**, including
  real adapter/mocked HTTP answer-schema wiring, citation forgeries, durable
  reservations, unknown holds, post-send settlement failure, no automatic repeat,
  incomplete pilot rejection, changed bindings and byte-preserving exports.
  These tests do not count as live observations.
- Verified manifest SHA-256:
  `3dc7a9fa647a5d86aca11003d196487f52cf521fa6c691b7a43c953e04a8faab`;
  **194 bindings**, 120 jobs and 12 deterministic skips. The pilot has 31 possible
  physical calls; the disjoint remaining phase has 77.
- Read-only cumulative ledger check: **215 reservations**, **$5.63403370**
  accounted, **$4.36596630** remaining under $10, including unchanged
  **$0.50135040** unknown-charge holds. These are the pre-pilot totals, not the
  current balance; the pilot report records subsequent paid activity.
- Both persistent journals and exported raw journals are ignored by Git. No
  dependency, frozen PO artifact, historical result or ledger policy was changed.

The subsequently executed C01 invocation completed S07's generation population.
S08 semantic review remains incomplete; these preparation tests establish no
semantic answer-quality result.

The original stopped invocation is retained unchanged. Its journal digest is
`1fa806c4d28dec0563c4cdf3d09d67f4413f374c28e3814985c85744db7ba042`.
The final two jobs, Q38/BM25 and Q38/vector, were not sent: $0.354399 already
spent plus the next $1.646592 reservation equals $2.000991, above the approved
$2 phase allowance. This was a reservation-headroom stop. A subsequent separately
approved R01 invocation completed those two jobs, preserving the original $2
profile and stopped journal. No billed job was repeated.

## Fixed experiment

`config/retrieval/P03-E03-profile-v1.json` selects Gemini 3.5 Flash through
Google AI Studio, temperature 0, top_p 1 and 8,192 output tokens, with provider
default reasoning. The allowance includes reasoning; actual usage/raw envelopes
are retained. The model alias and route are pinned, but the provider does not
publish a weight digest. Endpoint metadata is refreshed before each invocation.

All 40 frozen questions have three arms: no context, BM25, and saved real Qdrant
context. BM25 uses the verified E01 protocol. Vector evidence is reused from
I01's real queries, identified by report SHA-256
`f8388bdaae0a40cf045f0d69ff9dee67a7e20fb215864e37a56e534347d47604`.
Every source quote, scope and effective version is revalidated before each call.
This experiment measures generation on those saved contexts; it does not rerun
encoding or Qdrant and does not measure new live retrieval latency. E02/I01
retain the corresponding retrieval/resource evidence.

The separate answer schema has answer status, text and up to eight cited claims.
It is unrelated to PO output objects. The existing adapter's legacy wire schema
name is only a transport label: the actual supplied schema is the answer schema.
No-context may answer from knowledge as **unverified**. RAG empty/conflict cases
skip generation; irrelevant nonempty contexts still reach the model. There is
no relevance-label filter or removal of inconvenient jobs.

`config/evaluation/P03-E03-rubric-v1.json` contains independently authored
technical propositions and the correctness/grounding rubric. It is hashed before
generation and never supplied to the model. Mechanical checks reject malformed
JSON, duplicate keys, invalid status/claim structure and citations outside the
supplied identity/revision/hash/span set. They do **not** grade entailment or
correctness. Actual semantic review and adoption conclusions remain S08 work.

## Operations and approval

### Executed remaining28 invocation

The separately bound [C01 entrypoint](../../tools/answer-continuation/README.md)
reconstructs both pilot journals, verifies the joint receipt and known ledger
charges, then selects exactly the disjoint 84 remaining jobs. There are 77
possible calls and seven deterministic skips; all 36 pilot jobs are reused.
No original stopped record or generation control is edited. Semantic answer
quality is not a continuation selection criterion.

The approved **$3 new-phase allowance** provided reservation headroom under the
unchanged $10 cumulative cap. Before this invocation, $5.99963020 was accounted,
leaving $4.00036980, with the old $0.50135040 unknown holds preserved. Based on
pilot usage the estimated actual cost is about $0.91; it is not a cost guarantee.
The same per-call $1.646592 reservation, provider-enforced full context,
180-second request/7,200-second phase deadlines and zero retries/corrections apply.

```sh
make answer-continuation-check
make answer-continuation-plan
# Requires separate approval of this concrete paid invocation:
make answer-continue ARGS='--allow-provider --allow-server-context'
make answer-continuation-export
```

C01 completed its 84 jobs with 77 calls, 76 structurally valid answers, one
provider-error response and seven deterministic skips. Actual reported cost was
$0.761469; no budget/dependency stop occurred. No pilot job was rerun. The
provider-error observation is Q07/BM25 (network interruption, reported zero
tokens/cost), retained without retry. Full operational reconstruction verified
all 120 jobs across the three immutable journals and their known paid charges.

The commands above document the completed invocation: **do not rerun** the paid
command or recreate its frozen identity. Existing journal/paid-key guards reject
a repeat. The original `answer-run --phase remaining` path still rejects its
stopped parent; it is not a substitute rerun path. Export is idempotent for
identical saved bytes. All three journals remain separate.

### Original preparation and pilot controls

Run from the repository root; all Python runs in Docker. Saved I01 evidence must
be present locally at `results/submission/P03-I01-v1/report.json`. A missing or
changed file fails closed. No command starts Docker Ollama or Qdrant.

```sh
make answer-plan
make answer-plan ARGS='--phase remaining'
make answer-metadata
make answer-check
make check
make answer-freeze
```

Planning is network-disabled and makes no model call. Metadata reads only the
public provider catalog. Freeze creates `config/retrieval/P03-E03-v1.json` once,
binding source code, runtime, references, rubric, prompt, profile, schema and all
120 job contexts. Never overwrite it after generation. Changes require a new
experiment identity and matched rerun decision.

The fixed pilot has three questions from each case group: Q01/Q06/Q12,
Q13/Q18/Q23, Q25/Q29/Q32, Q33/Q35/Q38. Its 36 jobs include five deterministic
skips, leaving at most **31 physical calls**. The remaining phase has 84 jobs;
it must reuse the saved pilot, not rerun those 12 questions.

The original profile specified a $2 phase allowance. The separately approved
financial addenda used $2.10 total pilot exposure for R01 and a $3 new-phase
allowance for C01, within the existing $10 cumulative ledger. All retained a
7,200-second phase deadline, a 180-second request deadline, zero retries and
corrections. The existing ledger was never initialized, reset or raised.
The MATRIX stage is reused solely as the legacy funding bucket; E03 purpose,
phase and profile remain explicit in the journal. Paid approval must authorize
this use and E03-specific provider-enforced context admission. Past extraction
approvals do not authorize it.

The 2026-11-10 public catalog check confirmed a 1,048,576-token context and
65,536-token endpoint output ceiling. The profile reserves the full context at
$1.50/M input plus 8,192 output tokens at $9/M, including reasoning: **$1.646592
per call**, then settles reported actual cost. It disables compression, route
fallback and tools. There is no certified local prompt-token count. Rates and
the route are rechecked before execution. These are reservations, not predicted
costs. [OpenRouter pricing](https://openrouter.ai/google/gemini-3.5-flash/pricing).

Only after separate approval of this concrete pilot and allowance:

```sh
make answer-run ARGS='--phase pilot --allow-provider --allow-server-context'
```

Unknown charges retain their reservation and stop later calls. Unsafe pricing,
identity mismatch, fatal/dependency failures, exhausted funds and deadlines also
stop work. No automatic replacement invocation runs after a stop. Fixed phase
files, an execution lock and existing ledger request keys prevent accidental
repeat execution. Interrupted or stopped pilots cannot unlock continuation.

## Inspect, preserve and continue

### Two-job financial recovery

Following the user's acceptance of the tiny overage and separate concrete
paid-invocation approval, **P03-E03-R01** executed
for Q38/BM25 and Q38/vector only. Its separately frozen operational entrypoint
reuses the unchanged `AnswerRunner`; the original application/profile/manifest
and stopped journal remain byte-identical. It used **$2.10 total pilot
exposure**, counting the original $0.354399 rather than charging it again. All
model, prompt, schema, evidence, sampling, reasoning, deadline and retry settings
remain unchanged. Ten focused recovery tests, lint and strict typing passed;
offline planning verified the exact two-job membership with zero inference.

```sh
make answer-recovery-plan
# Requires separate approval of this new paid invocation:
make answer-recover ARGS='--allow-provider --allow-server-context'
make answer-recovery-export
```

The [operational entrypoint](../../tools/answer-recovery/README.md) has its own
profile and controller/test/Compose bindings. No remaining28 job is selectable.
The recovery made two calls for **$0.0111975**, with both replies schema/citation
valid and reporting insufficient evidence. Joint operational verification has
accounted for all 36 jobs and 31 unique physical observations. Semantic review is
pending. The recovery command cannot be rerun under a new output filename or after
deleting its journal: existing paid reservation keys also block a repeat.

The joint receipt SHA-256 is
`2f429d7f1f58bdede7a9a066c5a72557cd544481b2963480b00108b066d42445`.
It grants no remaining28 approval by itself. The original stopped-parent gate was
preserved; C01 verified the joint receipt and ran only after its own concrete
paid-invocation approval.

### Original journal and continuation gate

Journal events live in the existing named results volume under
`results/answer-runs/P03-E03-v1/`. Requests/admission/reservations are flushed
before send; raw physical results are flushed before settlement. Unexpected
exceptions retain unresolved reservations. Full planned membership stays in the
start event even if a process terminates early.

Export without network, credentials or inference:

```sh
make answer-export ARGS='--phase pilot'
```

This copies exact bytes to ignored
`results/submission/P03-E03-v1/pilot.jsonl` and prints their digest. A different
existing export cannot be overwritten. Review integrity/operational stops;
do not select continuation based on a convenient answer score. Schema-invalid,
refused and truncated responses are observations, not cases to drop.

After a complete eligible pilot and **separate approval** of the remaining
invocation, use its actual reviewed digest:

```sh
make answer-run ARGS='--phase remaining --pilot-sha256 REVIEWED_PILOT_SHA256 --allow-provider --allow-server-context'
make answer-export ARGS='--phase remaining'
```

**This original continuation command is currently blocked:** the saved parent has a
`phase_allowance_insufficient` stop. Its digest must not be used to bypass that
stop. The approved recovery and C01 continuation are recorded alongside it;
C01 verified both pilot receipts instead of erasing the original stop.

The command verifies exact pilot membership/profile, physical accounting and
settled reservations in the cumulative ledger. A changed model, prompt or policy
requires a new matched experiment; it cannot be stitched into these outcomes.
All non-skipped jobs now have real recorded replies or explicit physical failure
outcomes, completing S07. S08 review/replay and S09 archival remain
separate gates. Raw journals stay ignored; reviewed compact summaries belong in
Git, with full evidence archived through the existing workflow at S09.
