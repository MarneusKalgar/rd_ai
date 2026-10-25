# Large-document output allowance experiment — 22 October 2026

**Evidence retrieval:** Bulk evidence is in the [submission-history archive](../../archive-index/31349837ab5acff7f512d02ef2ee56a93a7a2da63d01dd8a12ea85acd734288a.json). Follow the [restore instructions](../guides/archiving-results.md#historical-submission-evidence) before opening restored-file links. Original run IDs and export paths retain their historical meaning.

The user approved a second native experiment for **B02-S008-PO01** with an
8,192-token output allowance. It completed with one failed, truncated attempt.
Doubling the allowance did not produce a complete extraction.

## Configuration and execution

The separate [configuration](../../config/experiments-output-8192.yaml) preserves
the baseline prompt, temperature 0, top_p 1, timeouts and execution policy.
It changes the output allowance to 8,192 and names the sampling variant
`output-8192`. The original configuration and recorded 4,096-token run remain
unchanged. Only the explicitly selected local model and input were executed;
no provider inference occurred.

```sh
make hw01-run MODE=native ARGS='--config config/experiments-output-8192.yaml --model local --input B02-S008-PO01 --stage smoke --run-id native-large-8192-20261022'
make hw01-export-run ARGS='native-large-8192-20261022'
make hw01-verify-export ARGS='native-large-8192-20261022'
```

These commands record the completed invocation; the run ID cannot be reused.
The configuration SHA-256 is
`3ff38ec6c46895a511db5c63179f57407d77024754e7458fdd2edd125a3d9e07`.

## Observations

| Measurement | Original native run | Second native run |
| --- | --- | --- |
| Ollama version | 0.40.3 | 0.40.7 |
| Output allowance / consumed tokens | 4,096 / 4,096 | 8,192 / 8,192 |
| Input tokens | 22,276 | 22,276 |
| Input duration | 169.006 s | 290.696 s |
| Prompt evaluation | 56.415 s | 56.030 s |
| Output evaluation | 112.336 s | 229.219 s |
| Attempts | 1 | 1 |
| Outcome | Truncated | Truncated |

Input, prompt, schema and model-digest identities match the original record.
The second run loaded the same Q4_0 Gemma weights with 32,768 context and
reported GPU memory placement. Its render-only admission bound was 22,278
tokens: **22,278 + 8,192 = 30,470**, within the available context. Setup loading
took 6.198 seconds separately from input duration. Prompt-cache count was zero.
Output evaluation averaged approximately 35.7 tokens/second.

Ollama returned `done_reason: length`. The JSON ended inside a field name;
validation retained an unterminated-string syntax issue. The runner preserved
the partial response as `failed / truncated`, without repair, correction or
another generation. The run manifest is complete with one failed record,
zero successes and no budget/dependency stops. CLI exit status 1 (Make exit 2)
therefore represents the extraction failure, not interrupted execution.

The runtime versions differ, so this is not an isolated timing measurement of
the output allowance. No live 4,096-token rerun on 0.40.7 was added.

## Content clue and next experiment

The prepared input is a catalogue-style order sheet with **13 rows containing
nonblank quantities**. Diagnostic text counts in the partial response find
92 product-name fields and 81 null product-quantity fields. For example, article
`96062` has a blank input quantity but appears in the generated item list.
These are observations of incomplete text, not a repaired JSON extraction or
an accuracy score. They suggest the model is including unselected catalogue
rows despite the v1 instruction to exclude catalogue and lookup rows.

A useful next experiment is a separately versioned prompt that makes ordered-row
eligibility explicit for this layout. Increasing the allowance again would not
address that selection behavior. An allowance of 16,384 would also exceed the
current context with this input; any such experiment needs a fresh context and
resource decision. No additional experiment is scheduled.

## Retained evidence

The [verified export](../../results/restored/31349837ab5acff7f512d02ef2ee56a93a7a2da63d01dd8a12ea85acd734288a/submission/native-large-8192-20261022/)
contains the manifest, record, checkpoint/admission evidence, raw response,
schema and hash inventory. Export and independent offline verification both
reported one record in a complete run. Logs and configuration copies are saved
under ignored `results/smoke-runs/native-large-8192-20261022/`, with `SHA256SUMS`.
The [original native evidence](native-runtime-verification.md) remains unchanged
apart from a link to this follow-up.
