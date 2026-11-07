# Model fundamentals through the saved experiments

These explanations use inherited experiments, not current provider capability
or pricing guarantees. No new model inference was required for P01.

## Tokens, context and output are separate limits

Inference consumes a formatted prompt and generates output tokens. Input
characters, bytes and tokens are different units. Tokenizer/template identity
therefore belongs in admission evidence. Prompt, schema, formatting, reasoning
where applicable and completion allowance must fit the selected runtime's
context policy. A larger context window does not force concise or correct output.

The output allowance bounds completion, not input capacity. Raising it can
avoid a truncated answer while also permitting more erroneous rows, increasing
latency and reserving more provider funds. The saved 4,096, 8,192 and 16,384
experiments demonstrate why the setting needed investigation; none establishes
a universal minimum for purchase orders. See the [output experiments](../reports/output-allowance-experiment.md),
[stronger-model experiment](../reports/stronger-model-experiment.md) and
[largest-input diagnostic](../reports/native-large-context.md).

Thinking/reasoning and final answer text can consume the available completion
budget differently. The native thinking-disabled rebaseline was a distinct
intervention, not permission to merge it silently with thinking-enabled runs.
Provider default reasoning remained part of its recorded conditions. Do not
request private reasoning content as verification evidence.

## Sampling and structured output

Temperature and top_p change token selection, not the schema or factual ground
truth. Temperature zero does not promise identical results across runtime/model
updates or all hardware. A combined sampling change is a combined intervention;
it cannot identify either parameter's separate causal contribution.

Schema-constrained output and validation enforce structure/types, while facts
and ordered-row selection can still be wrong. An extra catalog row may be fully
schema-valid. A failed or truncated object does not become correct by rescuing
its expected-null fields. The [scorer](evaluation.md) compares exact values and
positional lines without repair, sorting or normalization.

## Models and deployment

Model name, nominal size, quantization, runtime, prompt, task representation and
output budget all affect observed behavior. Providers do not necessarily publish
parameter counts, so a Flash/Gemma name comparison does not establish equal
model size. Strong performance on reused gold10 is a development result, not
unseen-layout reliability or proof of all local/cloud model families.

Native Ollama on this Mac and Docker CPU inference were different deployment
conditions. Native acceleration can change runtime performance without solving
row-membership errors. Historical [runtime comparison](../reports/local-runtime-comparison.md)
records the actual measurements and limits; P01 does not introduce a new speed
ratio. Local API cost zero excludes hardware, electricity and review time.

## Interpretation of P01's saved comparison

Gemma v2's primary gold10 score improves from 164/3494 to 198/2766. Those
denominators differ because extra rows decline from 394 to 303. On the fixed
342 gold field paths there are 46 wrong-to-correct and 12 correct-to-wrong
transitions. Headers improve from 61/70 to 68/70, while line selection remains a
major failure. The correct conclusion includes gains, regressions and row errors.

All thirty inputs remain operational observations; twenty still have no factual
labels. Source/layout exposure and repeated gold use prevent an independent
generalization claim. P01's [protocol guide](../guides/evaluation-protocols.md)
explains the paired populations and unavailable review judgments.
