# Provider exploratory matrix continuation

## Approved execution

On 26 October 2026 the user approved two sequential paid invocations: all thirty
frozen inputs with v1, then all thirty with v2. Both use Gemini 3.5 Flash through
google-ai-studio, temperature 0.2, top_p 0.9, 16,384 output tokens and unchanged
default reasoning. Full inputs and schema are preserved, with previously approved
provider-enforced matrix context and no compression or fallback.

Live public metadata and exact membership were checked before execution. The
route advertised 1,048,576 context tokens, $0.0000015 per input token and
$0.000009 per output/reasoning token. The full-context reservation is $1.720320
per physical call; it settles to reported actual cost, retaining unknown-charge
reservations. The cumulative ceiling remains $10. At approval $3.52909660 was
accounted and $6.47090340 remained, including retained earlier unknown charges.
The existing budget and dependency guards remain active. Each invocation permits
thirty primaries and at most 120 physical calls including bounded retries and
corrections; approval does not authorize a replacement invocation.

Run IDs:

- `matrix-provider-v1-exploratory-20261026-72`
- `matrix-provider-v2-exploratory-20261026-72`

## Verified results

All sixty new provider observations have attempted terminal records. Required
membership is **240/240**, covering eight complete thirty-input variants.
Failures, if present, count as attempted observations; completeness is distinct
from extraction quality. No native inference was repeated.

The table compares the frozen gold10 development cases. Schema validity covers
all30 inputs; the other twenty inputs have no gold labels. Baseline rows retain
the committed comparison checkpoint; native exploratory rows retain the verified
native report. The new provider exploratory rows were regenerated from original
records and independently reproduced after archive restoration.

| Model | Prompt | Sampling | Schema-valid / 30 | Gold correct / comparisons | Gold accuracy | Exact gold docs | Extra gold rows |
| --- | --- | --- | ---: | --- | ---: | ---: | ---: |
| local | v1 | baseline 0 / 1 | 29 | 164/3494 | 4.69% | 0 | 394 |
| local | v1 | exploratory 0.2 / 0.9 | 28 | 105/2542 | 4.13% | 0 | 275 |
| local | v2 | baseline 0 / 1 | 29 | 198/2766 | 7.16% | 1 | 303 |
| local | v2 | exploratory 0.2 / 0.9 | 30 | 197/2214 | 8.90% | 1 | 234 |
| provider-flash | v1 | baseline 0 / 1 | 30 | 278/342 | 81.29% | 1 | 0 |
| provider-flash | v1 | exploratory 0.2 / 0.9 | 30 | 267/342 | 78.07% | 1 | 0 |
| provider-flash | v2 | baseline 0 / 1 | 30 | 342/342 | 100.00% | 10 | 0 |
| provider-flash | v2 | exploratory 0.2 / 0.9 | 30 | 342/342 | 100.00% | 10 | 0 |

Extra predicted rows contribute wrong field comparisons, so score denominators
vary. Compare correct counts, row counts and operational failures together.
Gold10 was used during development and is not a held-out generalization estimate.
A perfect score would mean exact agreement on these labels, not proof of
reliability across the unlabeled corpus or unseen documents.

## New provider operations and spending

| Prompt | First valid | Final valid | Physical calls | Corrected inputs | p50 seconds | p95 seconds | Known API cost | Unknown-cost calls |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| v1 | 30 | 30 | 30 | 0 | 15.43 | 33.45 | $1.20104190 | 0 |
| v2 | 30 | 30 | 30 | 0 | 9.32 | 29.30 | $0.90389520 | 0 |

Measured processing time and gold field populations:

- v1: 8m 40s summed input processing; present fields 193/197; null fields 74/145. Retained failures: [].
- v2: 5m 57s summed input processing; present fields 197/197; null fields 145/145. Retained failures: [].

Processing time excludes container/setup work and includes bounded corrections/retries.

Accounted spending changed from **$3.52909660** to
**$5.63403370**, a delta of **$2.10493710**.
Remaining cumulative allowance is **$4.36596630** under the $10
ceiling. Accounting includes retained earlier unknown-charge holds; it is not
synonymous with known billed API cost. Previous reservations were preserved.

The [archive index](../../archive-index/8ca6d7d755546c6fcea7e6c09cee7f152288f8d787942790350b54dd9d5cbcce.json),
[Garage receipt](../../archive-index/8ca6d7d755546c6fcea7e6c09cee7f152288f8d787942790350b54dd9d5cbcce.remote.json) and
[restore verification](../../archive-index/8ca6d7d755546c6fcea7e6c09cee7f152288f8d787942790350b54dd9d5cbcce.verification.json) retain the
complete required source provenance and preparation/evaluation records. Every
source/restored payload matched and both new provider evaluations reproduced
exactly. Selection: `provider-exploratory-results`. Raw bundles remain ignored;
compact indexes, verification and this report can be versioned.

Required matrix execution is complete. Final analysis, reproducibility and
acceptance work in sections 8–9 remain separate tasks. No additional paid
invocation, repetitions or optional model experiments are approved here.
