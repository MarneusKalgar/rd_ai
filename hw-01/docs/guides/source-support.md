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

`config/gemma-raw-fallback.yaml` selects a third, separate profile,
`ordered-rows-raw-fallback-v1`. Its supported layouts use the identical selection
and cell-record body. When selection abstains, the request receives the exact
original source text, including line endings and unparsed content. It introduces
no new layout support. A source hash equal to the rendered hash is expected on
the raw fallback branch; the hybrid profile still has its own evaluation identity.

`config/gemma-field-roles.yaml` selects `ordered-rows-field-roles-v1`. It preserves
the hybrid body and appends source-derived identifier/date role cues only when a
closed cell-label audit can resolve their scope. It does not read gold or model
outputs, rewrite extractions, change the v2 instruction file or add a retry loop.
The added context has a distinct workflow identity and enters full admission.
Its first gold10 trial regressed overall; see the
[source-field role report](../reports/source-field-roles.md). Keep it as an
experimental configuration rather than replacing the measured raw-fallback
hybrid. Detection findings remain useful offline and do not enforce acceptance.

`config/gemma-scoped-roles.yaml` selects `ordered-rows-scoped-roles-v1`. It
requires the unchanged row selector to establish membership before rendering
role cues. It matches the selected source product-cell references against the
field-role audit and exposes only those rows' facts. Unsupported or ambiguous
membership leaves the hybrid body untouched with no cue; repeated ordered
products remain in the body even when their role matching is ambiguous. No
layout recognition is added and null quantities are not globally filtered.
Scope decisions and exact source-cell references enter manifest provenance and
reload validation. The original unscoped profile remains reconstructible.
Its first gold10 trial scored 80.60% versus the raw-fallback hybrid's 77.05%,
with unchanged row errors and one exact document. See the
[measured scoped-cue report](../reports/scoped-role-cues.md) before considering
continuation. This tuned development result does not certify unseen documents.

The offline `assess-source` report version 2 includes field-role findings beside
the original row/quantity checks. Exact, unique product matches connect returned
fields to source rows. Generic article codes alone do not establish buyer-owned
identifiers; header delivery/service dates alone do not establish line dates.
Explicit buyer codes and dates on the product's own row are retained verbatim;
ambiguous date formats, shared critical cells, conflicting roles, unknown labels,
free-text scope qualifiers and duplicate/paraphrased descriptions require
abstention. Blank explicit fields resolve to null, but absent output keys do not
earn supported findings. A supported role does not prove ordered-row membership
or full PO correctness. These checks currently cover declared neutral labels,
not arbitrary languages or documents.

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
