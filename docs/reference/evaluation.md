# Offline evaluation — shared core for 7.1 and 8

`make evaluate ARGS='run-id ...'` reads saved terminal runs in the persistent
Docker results volume. It loads the approved corpus, revalidates record/schema/
checkpoint hashes and identities, and prints evaluation JSON. It has no network,
credentials, model initialization or generation. Redirect its output to retain a
report. Original runs and the cumulative ledger are never rewritten.

`evaluate --budget-policy config/evaluation-budget-policy.json` uses an explicit
public, manifest-bound historical cap revision instead of the private ledger
audit. The two modes are mutually exclusive. Only the administrative cap is
normalized; source manifests must match the policy and every other control stays
in the grouping identity. The result retains the policy hash and original run
policies. This affects read-only evaluation only. See the
[ledger-free reproduction workflow](../guides/reproducing-results.md).

## Quality rules

The frozen JSON Schema supplies the seven header fields and eight line fields;
there is no second PO model. Values are compared exactly after contract
validation. No trimming, case folding, decimal-string coercion, sorting,
deduplication or repair is applied. For example, `159` and `159.0` are distinct
string representations in this evaluator. This conservative rule is explicit
and consistent across candidates and prompts.

Line matching is positional because the contract requires source order. Repeated
products remain separate rows. A missing row loses all eight matches; an extra
row adds eight wrong comparisons. A shifted/reordered row can also lose matches
at later positions. Counts of missing/extra rows report length differences, not
an inferred product alignment. The scorer retains mismatched field paths.

For each document, the primary denominator is
`7 + 8 × max(expected line count, valid predicted line count)`. Sum correct and
total fields across labeled documents before dividing. Report header, ordered
line and per-field results, exact-document counts, and separate expected-present
and expected-null denominators. Extra rows are penalized in the primary/line
scores; the present/null subsets describe gold fields only. Failed, truncated,
invalid and untouched labeled outputs earn zero matches, including expected-null
fields. Partial invalid JSON is never parsed into a rescued quality score.

Only approved gold cases receive factual accuracy scores. The other 20 inputs
contribute operational metrics and qualitative observations. Screening/tuning
on the gold set makes later scores development-set measurements; they are not
independent held-out generalization results.

## Operational rules

- Validity and correction rates use all selected input records, including failed
  and untouched outcomes. First validity refers to the first physical attempt;
  final validity includes the one allowed correction.
- Latency uses retry-inclusive coordinator duration for inputs with at least
  one physical request, including failures. Untouched inputs add no synthetic
  zero-latency sample. Report sample count and nearest-rank p50/p95
  (`sorted[ceil(q × n) - 1]`); empty populations yield null. Setup/build time is
  excluded. Ten observations support only a small-sample description.
- Sum known paid attempt charges, including failed requests, retries and
  corrections. Any unknown paid charge makes total cost and cost per 1,000 null;
  the known sum remains a lower bound. Cost per 1,000 scales by attempted input
  count. API reservations are reported separately and are not billed cost.
  Local API cost is zero; machine, electricity and time costs are excluded.

## Evidence boundaries

### Explicit sampling-ID reuse

`evaluate --sampling-aliases config/matrix-sampling-aliases.json` enables the
reviewed diagnostic-to-matrix naming map. Source and target temperature, top_p
and output allowance must match exactly; conflicting targets, ambiguous sources
and alias chains are rejected. Saved source settings are checked against the
declared map before grouping. All other variant identities remain distinct.
Original records and hashes remain unchanged, and reports retain each source
sampling value alongside the canonical grouping identity. Duplicate inputs in
the resulting variant remain errors, including overlaps introduced by an alias.

Matrix membership embeds the same validated map and identifies a differing
`source_sampling_id` explicitly. The archive verifier resolves the original
record key from that source ID, checks the canonical target and preserves the
original manifest/record hashes. Without a map, different sampling IDs continue
to be separate variants. Aliases never change generation requests or scores.

The [exploratory continuation](../reports/matrix-exploratory-preparation.md)
records the specific ten-observation promotion and remaining commands.

Variant groups retain stage, model ID/name, serving endpoint, actual local
runtime/digest, prompt hash, sampling, schema, execution policy and effective
context/tokenizer/processor evidence. Original run/config/manifest hashes and
reported provider model names remain visible. Different settings stay separate;
overlapping input observations for the same variant are rejected. Separate
repetitions explicitly rather than averaging them by accident.

Complete runs and stopped runs with terminal records for all selected jobs can
be evaluated. Incomplete state, untouched inputs, missing gold cases and unknown
accounting remain visible. Running/interrupted runs with checkpoint-only jobs
cannot produce this final aggregate; the command rejects them for separate
inspection rather than inventing missing outcomes or discarding those jobs.
Handling such unfinished checkpoint histories in a later report needs explicit
scope; the current evaluator never resumes or replays them.
