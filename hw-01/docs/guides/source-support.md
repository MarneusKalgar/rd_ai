# Assess source evidence and run isolated Gemma support trials

Source support has two independent uses. `assess-source` inspects saved outputs
without reading gold answers, changing their status, making model calls or
requesting corrections. Optional `source_view` configurations change the source
representation sent for a new, separately identified experiment.

## Offline assessment

From the repository root:

```sh
make hw01-assess-source ARGS='matrix-native-v2-gold-20261024-72 --source submission'
```

The report retains the existing ordered-row diagnostic and adds conservative
completeness and quantity findings. Exact, unique product descriptions support
source matching; paraphrased or repeated descriptions remain unknown. A known
positive source quantity can contradict a missing or different returned
quantity. This does not establish unit interpretation, printed precision or
correctness of the whole purchase order. Unsupported layouts and legitimate
unknown quantities must not be rejected by a universal non-null rule.

## Separate source views

`config/gemma-cell-records.yaml` selects `cell-records-v1`. It expands each
approved source row into a bracketed record with one cell per line, retaining
cell coordinates, labels, literal values, blank markers and source order.
Unknown lines remain present. No translation, examples, quantity conversion,
deduplication or row selection is added.

`config/gemma-ordered-rows.yaml` selects `ordered-rows-v1`. It applies the same
representation after a deterministic selection stage. Only three declared
order-form conventions are supported. It excludes explicit blank catalog rows
only when the entire recognized layout satisfies conservative checks. Unknown
quantities, unfamiliar headers, extra item markers or conflicting shared cells
cause abstention and retain the complete source representation. Headers and
shared unit cells remain available, including shared cells encountered only
inside an excluded catalog record. Repeated ordered products remain separate.

This selection stage uses source cells only. Gold answers and earlier model
predictions never enter it or the extraction request. It is deterministic
selection followed by one extraction request, not a second model reasoning
call or a post-processing repair of generated output.

Every new run retains the exact original source, rendered request source,
both hashes, source map, exclusion decision and implementation identity in its
manifest. Reload checks the representation and its binding to approved source
bytes. Evaluation separates raw, representation-only and selected-source
variants. Raw historical records and the frozen scorer remain unchanged.

Gold-only trials require explicit `--input` selections; the ordinary `run`
command defaults to the full corpus. The current authorization is gold10 only;
do not use these configurations to launch remaining20 automatically.

## Verification limits

The focused tests exercise preservation, sheet inheritance, shared context,
duplicate rows, abstention, evidence ambiguity, manifest tampering, CLI
generation and assessment without gold files. All tests run in Docker; native
Ollama remains the inference runtime. The three recognized layouts belong to
the development corpus. Their successful checks do not establish held-out
precision, recall or applicability to arbitrary purchase orders.
