# Load example resources into extraction instructions

The application can explicitly load a pinned skill package before constructing
generation requests. This is resource loading, not model-selected discovery,
tool use, execution of scripts or a new correction loop. The same rendered
instructions pass through the shared message serializer for both backends.

`PromptConfig.file` still identifies the base prompt in `prompts/`. An optional
`skill` identifies `prompts/skills/<package>/SKILL.md` and an ordered `resources`
list. Each file needs its exact SHA-256. Resource paths are project-relative but
must resolve inside that package, including when symlinks or aliases are present.
Duplicates, missing/changed/empty resources and directory escape fail before
model setup. References written inside content are inert; only declared files
are loaded. There is no recursive loader or hidden resource selection.

The rendered instructions preserve the exact base bytes, then add a stable
resource separator, SKILL.md and the requested resource contents in order. File
paths do not substitute for content. The fully rendered instructions enter
preflight/planning hashes, context admission and actual generation, including
the existing schema-correction request when needed. The authoritative PO schema
and source are separate request components and remain unchanged.

The manifest's `setup.prompt_resources` retains base/package/resource paths,
hashes, contents, explicit order and rendered instructions/hash. Reload and export
reconstruct those bytes and bind them to each job's prompt hash without needing
the current package files. Plain prompts omit the optional configuration field
when serialized, preserving historical experiment identities and reports.

## First experiment

`config/gemma-examples.yaml` selects `v2-examples`, frozen `prompts/v2.txt` and the
`extraction-examples` package. It keeps the scoped source view and native Gemma
profile: thinking=false, temperature 0/top_p 1, 49,152 context and 16,384 output.
The three fictional examples illustrate existing rules; their development
disclosure is in `prompts/skills/extraction-examples/README.md`, which is not
loaded. Examples were chosen with knowledge of gold10 failures; this is a
development experiment, not independent evaluation.

Compare all ten outcomes against the saved scoped primary run, without semantic
correction or selecting favorable fields from different outputs. Record validity,
matched fields/denominators, exact documents, extra/missing rows, present/null
accuracy, calls/tokens/time and any copied fictional example content. Never
filter example leakage out of predictions before scoring.

Use normal `plan-run`, `run`, `export-run`, `verify-export` and `evaluate`
entrypoints with this configuration and explicit input/run selections. A local
execution does not approve provider inference. Changing resources requires new
hashes and a separately identified experiment; never revise them after a run and
describe that run as using the new package.

The [measured gold10 report](../reports/gemma-examples.md) records the first
examples-only run and its mixed/negative result. Completion does not authorize
a second run or automatic example revision.
