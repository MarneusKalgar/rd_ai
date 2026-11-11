# E03 remaining28 continuation

Status: executed after separate approval on 2026-11-10. All 84 jobs are recorded:
77 calls, 76 structurally valid answers, one preserved provider-error response
and seven deterministic skips. Cost: $0.761469. No budget/dependency stop or
pilot rerun occurred. Do not repeat the paid invocation; journal and paid-key
guards preserve its single approved execution. See the
[full report](../../docs/reports/P03-rag-answers.md).

C01 is an operational continuation of the same frozen E03 generation experiment.
It reconstructs the 36 pilot outcomes from the unchanged initial and R01 journals,
checks the reviewed joint receipt, and matches all 31 known charges to the ledger.
The initial stopped record is preserved. Completed model observations and skips
cannot be replaced, repeated, or selected away because of answer quality.

The fixed remaining population has **28 questions × three arms = 84 jobs**:
77 possible physical calls and seven deterministic skips. All 36 saved pilot
jobs are reused, with no new pilot inference. Model, route, prompt, schema,
sampling, default reasoning, output allowance and context policy stay unchanged.

The approved **$3 phase allowance** was for new continuation spending under the
unchanged $10 cumulative ledger. The pilot is already accounted for globally;
it is not charged again or seeded into this phase's counter. Every call still
requires a $1.646592 reservation, then settles reported actual cost. Unknown
charges retain the reservation and stop later calls. No automatic replacement.
Deadlines remain 180 seconds/request and 7,200 seconds/phase, with zero retries
and corrections. No native inference, embedding or database execution is added.

```sh
make answer-continuation-check
make answer-continuation-freeze  # once, before inference
make answer-continuation-plan
# Only after approval of this exact paid invocation and allowance:
make answer-continue ARGS='--allow-provider --allow-server-context'
make answer-continuation-export
```

Offline services have no provider credentials or network. The controller/test,
profile, Compose overlay, joint receipt and exact remaining job population are
bound in `config/retrieval/P03-E03-C01.json`. Application source and the original
E03/R01 manifests are unchanged. The shared application runner owns physical
accounting, admission and failure policy; this entrypoint owns only composition,
receipt verification and explicit scheduling.

The new journal is `results/answer-runs/P03-E03-v1/remaining-C01.jsonl` in the
existing results volume; export writes the same filename under ignored
`results/submission/P03-E03-v1/`. Existing phase files and paid request keys
prevent repeating the invocation, including after accidental output deletion.
Model response structure/citation checks establish no semantic accuracy score.
