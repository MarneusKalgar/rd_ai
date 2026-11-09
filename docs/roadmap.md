# Document intelligence R&D roadmap

- Version: **1.14**.
- Created and source mappings reviewed: **2026-10-31**.
- Framework/SDK proposals reviewed: **2026-11-08**.
- Status: P00 and selected P01/P02 offline slices concluded; later capability studies remain conditional/planned.
- Implementation baseline: `654be96` — ledger-free report reproduction.

## 1. Authority and project outcome

`rd_ai` will evolve as one document-intelligence R&D application. It extracts
purchase-order fields, checks their source support, retrieves relevant rules
and proposes changes for human review. Research decisions use measured quality,
review burden, latency, resource use and cost. A useful negative result can
close an experiment without adding a permanent feature.

This is the canonical project roadmap in the versioned documentation tree.
It incorporates the local 2026-10-25 document-intelligence proposal and the later
decisions recorded in the extraction reports. It supersedes that proposal's
120/240 baseline, unfinished-matrix description and instruction to defer the
repository consolidation. Ignored assignments, discussions and working plans
remain historical inputs, not prerequisites for a fresh checkout.

P00 has consolidated the application at the repository root, preserving runtime
and evidence identity. See the [migration record](reports/P00-consolidation.md).
Canonical root commands are available; S08 subsequently retired `hw01-*` aliases. This
roadmap does not authorize new inference or later milestone execution.

Planning hierarchy:

- **Milestone P00–P05:** an observable capability or answered engineering question.
- **Implementation slice:** ordered changes with affected paths and acceptance
  criteria, specified in each milestone's dedicated plan.
- **Experiment:** a frozen question, comparison, data identity, changed factors,
  metrics, resource allowance, stop conditions and recorded decision.

Keep these identifiers stable. Historical section numbers, run IDs and prompt
versions retain their original meanings. Milestone status is planned, in
progress or concluded; a separate decision records adopted, rejected, deferred
or inconclusive outcomes. Existing evidence is marked inherited, rather than
claimed as new work under this roadmap.

## 2. Inherited baseline and limits

The following are recorded results, not new runs or current model-selection and
price guarantees. See the [consolidated report](../REPORT.md),
[extraction foundation flow](reference/extraction-foundation.md),
[historical matrix plan](plans/matrix-experiment.md) and
[section 9 verification](reports/section9-verification.md).

| Area | Inherited state | Planning consequence |
| --- | --- | --- |
| Corpus | Thirty approved neutral texts derived from Excel layouts; ten human-approved gold POs | Existing text evidence does not establish a general workbook parser. The other twenty remain unlabeled. |
| Required historical matrix | **240/240 attempted observations:** two models × two prompts × two sampling profiles × thirty inputs | Matrix execution is closed, including failed outcomes. There is no remaining 120-observation backlog. |
| Provider | Gemini 3.5 Flash v2 matched 342/342 fields and ten exact documents on development gold10 at both tested sampling profiles | A strong baseline on reused development labels; no unseen-data reliability claim. |
| Native | Gemma v2 baseline matched 198/2766 fields, with 303 extra gold rows; assisted identifier correction reached 309/366 and two exact documents | Preserve the distinction between model capability and source-derived assistance. Complete unattended extraction was not demonstrated. |
| Concluded local exercises | Qwen comparison, sampling diagnostics, source representations/selection, field-role cues, guarded correction, examples and header/line splitting | Reuse their positive and negative evidence. Further tuning needs a new concrete question, not repetition of the exercise list. |
| Deferred | JEV verification/routing, broader semantic correction, source cropping/chunking, further general prompt tuning | These were not implemented merely because they appeared in a plan. |
| Runtime | Shared contract validation, injected adapters, bounded retries/correction, deadlines, dependency stops, durable accounting and checked exports | Extend these responsibilities instead of building another harness. |
| Reproducibility | Saved-record aggregation, Garage archival/restoration and ledger-free matrix reproduction; recorded 938-test gate | Baseline reporting and reproduction are inherited. P00 verifies preservation after migration. |
| Data exposure | Gold10 informed model/prompt/workflow development | Report development gains honestly. Existing unlabeled cases inspected during experiments are not automatically a blind holdout. |

The ledger, unresolved charge holds, frozen inputs/gold/schema/prompts, source
manifests and archive identities remain authoritative. Historical spending is
not reset for the new project name. No new label approval is implied here.

## 3. Architecture and experiment rules

Keep one Python application and one dependency environment. Python, dependency
maintenance, tests and substantial scripting run in Docker. Native Ollama is
the selected exception for local inference; the removed Docker Ollama image and
weights are not restored implicitly. Keep the project independent of AspectLoop:
its product milestones, TypeScript/NestJS implementation and PDF-first scope
need their own decisions.

Application setup owns resources; adapters translate protocols; domain code
owns contracts and state transitions. Add ingestion, retrieval, review and API
modules when implementing them. No empty framework of future packages,
microservices, databases or deployment platforms is required.

Preserve the authoritative PO v1 schema. Source references, support verdicts,
proposal/approval metadata and execution records remain outside PO objects.
New field semantics require a new contract version and reviewed affected labels.
Human approval is a separate application action; the model never acquires direct
document mutation or submission authority through its output.

For each measured experiment, predeclare:

1. Question, inherited comparator, data/source groups and exposure history.
2. Changed factor or explicitly combined intervention; exact model, prompt,
   schema, representation and retrieval/tool identities.
3. Quality, failure and security metrics; numeric acceptance thresholds for
   adoption; call/token/time/spend bounds and stop conditions.
4. Exact commands and separate paid-invocation approval where applicable.
5. All selected outcomes, including failures, untouched inputs, unknown support
   and unresolved costs; evidence location and adopt/reject/defer decision.

Numeric thresholds must be set before a measured run, not fitted afterward.
Research can conclude with a rejected candidate; that does not satisfy an
unachieved capability acceptance criterion. A test count alone closes neither.

Use deterministic checks for structured facts and hard permissions. Measure
retrieval relevance, answer grounding, correction usefulness and security
separately. A model judge, if selected, needs a rubric, reviewed anchors and
false-acceptance/disagreement measurement. JEV remains a deferred candidate,
not the default judge or a prerequisite.

Additional documents are not assumed available. Reviewed labels on existing
inputs or synthetic challenge fixtures can support a declared development
experiment. Keep source/layout families together, disclose prior exposure and
never promote provider predictions to gold automatically. Gold answers, saved
predictions and evaluation reports must not enter a retrieval corpus used to
claim independent extraction quality. No data collection gate applies to P00.

### Framework and SDK experiments

Keep the existing Python adapters, execution coordinator, validation and durable
accounting as the baseline. Framework and SDK names describe overlapping
responsibilities; select a candidate for a concrete integration, orchestration
or evaluation question. Popularity and reference-project usage are not adoption
criteria, and a new library alone does not establish better extraction quality.

| Candidate | Milestone placement | Proposed comparison and boundary |
| --- | --- | --- |
| LangChain | Planned P03-I01 retrieval/composition trial; conditional P04 agent-loop comparison | Compare Qdrant integration and request composition with the direct implementation using the same filters, vectors, contexts and metered model capability. Adoption needs parity and a demonstrated integration benefit; no mandatory framework layer or additional live generation matrix. |
| LangGraph (Python) | P04 bounded orchestration experiment | After the fixed review workflow exists, compare the same steps/tools with explicit graph state, branching, checkpoints and human-review interrupts. Test recovery and replay before introducing a separately identified model-directed loop. |
| LangSmith | Conditional P04 trace/evaluation pilot; P05 operational assessment | Compare debugging, trace completeness and evaluation usefulness with existing saved records and portable instrumentation. It can be evaluated independently of LangChain/LangGraph; the ledger and archived evidence remain authoritative. |
| Vercel AI SDK | Separate AspectLoop TypeScript proposal | No rd_ai language migration or JavaScript runtime dependency. SDK Core integration and optional UI streaming belong to AspectLoop's own roadmap and acceptance process. |

The selected milestone plan must freeze comparable cases, model/prompt/schema
settings and predeclared quality, failure, latency, call/cost and engineering
criteria. Start integration/recovery checks with deterministic fixtures; any
live comparison needs its own approved scope and allowance. Keep model calls
inside existing admission/accounting controls, including framework retries and
replayed nodes. Checkpoints do not guarantee exactly-once external effects:
application authorization, document-version checks, idempotency and human apply
commands remain independently enforced. Define checkpoint ownership, retained
data and principal/document isolation before enabling persistence.

Tracing starts disabled. A LangSmith pilot needs an explicit data/export,
redaction, access, retention and cost decision, using synthetic or approved
neutral fixtures. Reject unauthorized payload/credential export and verify that
telemetry failure cannot change task outcomes or accounting. A bounded trial
does not select a second permanent observability stack. Record an
adopt/reject/defer decision. P03-I01 is selected bounded trial work; permanent
adoption remains conditional. Other unselected candidates need not be installed
or exercised to accept the underlying capability.

Primary references reviewed 2026-11-07:
[LangChain](https://docs.langchain.com/oss/python/langchain/overview),
[LangGraph](https://docs.langchain.com/oss/python/langgraph/overview),
[LangSmith](https://docs.langchain.com/langsmith/observability) and
[AI SDK](https://ai-sdk.dev/docs/introduction). See the
[living glossary comparison](reference/ai-ml-glossary.md#langchain-langgraph-and-langsmith)
for definitions and cross-project distinctions. This roadmap update authorizes
no dependency installation, trace export or inference.

## 4. Sources and meaning of topic coverage

Mappings use the [AI Engineer roadmap](https://roadmap.sh/ai-engineer), accessed
2026-10-31, and its publisher's
[topic content at revision 5a0a5314418aad4bded3ccdeea958e50d8386a5f](https://github.com/nilbuild/developer-roadmap/tree/5a0a5314418aad4bded3ccdeea958e50d8386a5f/roadmaps/ai-engineer/content).
The official topic index was checked at that revision. Topic labels below are
grouped for this project, not a reproduction of the visual roadmap's ordering.

Security mappings use the [OWASP Top 10 for LLM Applications, 2025 edition](https://genai.owasp.org/llm-top-10/),
accessed 2026-10-31. These are project-specific exercises mapped to a risk
taxonomy, not OWASP certification. Revisit the mapping when sources or the
application change; do not silently relabel historical evidence.

Each milestone lists **topics to exercise**, with inherited and conditional work
identified. A planned mapping is not completed coverage. Record scope, control,
fixture identity, observation, residual risk and evidence before marking an
exercise demonstrated. In particular, ordinary schema tests do not demonstrate
prompt-injection resistance, and local API tests do not prove production safety.

Security cases use fictional identities, synthetic markers and controlled
destinations. Pair prohibited actions with legitimate positive controls.
Deterministic tests assert authority/resource boundaries; model-dependent runs
measure both task quality and attack effects. A model may follow injected text
while application controls still prevent unauthorized effects; retain both
observations. Never require disclosure of private model reasoning as evidence.

## 5. Milestones

| Milestone | Outcome | Dependencies | Initial status |
| --- | --- | --- | --- |
| P00 | One project structure with preserved baseline and reproducibility | Existing saved evidence | Consolidation concluded; S08 runtime follow-up concluded |
| P01 | Explicit evaluation protocol and regression/challenge capabilities for the next question | P00 | Offline protocol/comparison scope concluded; judge study unselected |
| P02 | Inspectable source-grounded extraction and a measured support decision | P01's protocol for the selected experiment | Selected text-provenance slice concluded; workbook/semantic studies conditional |
| P03 | Versioned, authorized evidence retrieval and grounded answers | P01 protocol; an approved reference collection | E01/E02 exercised, including real embeddings/Qdrant; RAG generation and LangChain trial remain planned |
| P04 | Human-reviewed proposals with independently enforced application authority | P01; usable source evidence; P03 or controlled retrieval fixtures | Planned; LangGraph, agent/MCP and tracing comparisons conditional |
| P05 | A usable local interface and measured operational/release controls | A selected fixed workflow from P04 | Planned; deployable-service expansion conditional |

P02 and P03 need not wait for every possible P01 extension. P04 tool contracts
can start with controlled fixtures. Define a small experiment protocol before
each model-dependent slice; this is not a requirement for parallel implementation.
Evaluation, security and resource accounting continue through every milestone.

### P00 — Project consolidation and preserved baseline

**Question:** Can the existing application become the repository's single R&D
project without changing its measured behavior or losing evidence?

**Scope:** reconcile inherited work, align governance, promote the application
to the root, merge documentation and Make entrypoints, and verify the migration.
The [dedicated P00 plan](plans/milestones/P00-project-consolidation.md) supplies
ordered work, compatibility rules, commands, rollback and acceptance criteria.
Its added S08 separates removable command/descriptive names from optional
environment/package/storage migrations and preserved historical formats.
The low-risk cleanup is concluded. The subsequent S08 request selects DI
settings, package metadata and disposable Compose naming while retaining
persistent/archive identities. See the [runtime migration record](reports/runtime-name-migration.md).

**AI Engineer topics exercised**

| Topics | Project exercise and evidence |
| --- | --- |
| Choosing the Right Model; Impact on Product Development; Roles and Responsibilities | Inherited comparison informs the useful project boundary; no new model selection is implied. |
| LLM Evaluations; Deterministic Evals; Evaluation Metrics; Regression Testing | Preserve and reproduce the existing matrix after migration; verify a deliberately wrong report/control still fails. |
| Cost/latency monitoring | Preserve measured populations, usage and accounting identities; disclose native machine/review costs excluded from API charges. |
| Security and Privacy Concerns; Constraining outputs and inputs | Verify the root Docker context, private-material exclusions and separation of offline verification from inference. |

**OWASP topics exercised**

| Risk | Bounded P00 exercise |
| --- | --- |
| LLM02 — Sensitive Information Disclosure | Keep private inputs, settings and ledger contents out of Git/images/public archives during the move; use inert exclusion canaries and existing fixture triage. |
| LLM03 — Supply Chain | Verify frozen artifact, manifest, dependency/image and archive identities; test changed evidence rejection and exact restoration. |
| LLM09 — Misinformation | Retain gold exposure, unsupported-generalization and known/unknown-support disclosures; report reproduction verifies measurements, not truth of unseen outputs. |
| LLM10 — Unbounded Consumption | Keep offline commands network-disabled and model-free; preserve retry/deadline/spending safeguards and named accounting storage without new calls. |

**Acceptance:** one discoverable roadmap and runnable root application; exact
baseline preservation; canonical and compatible Make routes; private boundaries
intact; full offline checks and isolated reproduction pass. P00 introduces no
new inference, labels, dependencies or application capability experiments.

### P01 — Evaluation protocols and model fundamentals

**Question:** How will the next change demonstrate useful improvement rather
than better agreement with repeatedly reused examples?

The [P01 implementation plan](plans/milestones/P01-evaluation-protocols.md)
records concluded S01–S07 execution: offline comparison verification using
saved evidence and finite technical controls, with zero new model calls. See the
[P01 execution report](reports/P01-evaluation-protocols.md). Judge calibration,
new human semantic judgments and live attack susceptibility remain unexercised.
Completion does not authorize later inference or milestone execution.

**Inherited:** scorer arithmetic/failure handling, per-field and present/null
metrics, sampling/output/context observations, false-positive diagnostic work
and ledger-free reproduction. Do not rebuild or rerun them as new foundations.

**New bounded work:** define exposure/source-group rules, reviewed error and
no-change/abstention rubrics, paired comparison/error-category reporting where
missing, and a predeclared experiment record. Add reviewed cases when available;
otherwise label synthetic or existing-case challenge suites honestly. Explain
tokens, context/output and sampling using saved observations. A judge calibration
study is a separate conditional experiment.

**AI Engineer topics exercised**

| Topics | Project exercise and evidence |
| --- | --- |
| How LLMs Work; Tokens; Context Window; Inference | Explain recorded admission/output failures and cost with saved examples; no foundation-model training required. |
| Temperature; Top-P; Structured Output; Choosing the Right Model; Self-Hosted Models | Interpret inherited controlled profiles and schema-valid factual errors; avoid claiming unpublished provider parameter sizes or model-family limits. |
| LLM Evaluations; Deterministic Evals; Human Evals; Evaluation Metrics; Regression Testing | Version rubrics/cases, disclose exposure and source groups, and prove scoring/reporting sensitivity to wrong outputs. |
| Model-Based Evals | Conditional calibration against reviewed anchors; measure disagreement and false acceptance before adoption. |
| Prompt Injection Attacks; Conducting Adversarial Testing | Define benign/attack pairs and distinguish model behavior from application boundary enforcement. |

**OWASP topics exercised**

| Risk | Bounded P01 exercise |
| --- | --- |
| LLM01 — Prompt Injection | Synthetic document instructions attempt to override extraction rules; retain task errors and separately asserted prohibited effects. |
| LLM02 — Sensitive Information Disclosure | Synthetic context markers and redaction tests distinguish legitimate task data from cross-case leakage. |
| LLM05 — Improper Output Handling | Test hostile schema-valid values at downstream interpretation boundaries; structural validity does not imply safe use. |
| LLM07 — System Prompt Leakage | Exercise extraction attempts with harmless markers; prompts contain no credentials or authorization authority. Disclosure must not grant access. |
| LLM09 — Misinformation | Wrong-but-valid outputs, null/present errors, unnecessary corrections and judge false acceptance receive explicit metrics. |
| LLM10 — Unbounded Consumption | Controlled long/failed cases retain request/step/token/time/spend ceilings and unknown charges. |

**Acceptance:** a selected next experiment has explicit data/exposure identity,
review rubric, metrics/thresholds, resource bounds and failure policy; needed
evaluation extensions have independent arithmetic/negative controls. Missing new
documents limit claims, not all future engineering. Judge coverage remains
unexercised unless that optional study actually runs.

### P02 — Spreadsheet understanding and source grounding

**Question:** Which source representation or support mechanism improves usable
field/row extraction, and what review burden does it introduce?

The [frozen P02 implementation plan](plans/milestones/P02-source-provenance.md)
selected P02-E01: offline field-to-source byte references on the thirty saved
native v2 baseline records. Its execution covers PO-number occurrence candidates
and identifier/date linkage to inherited role checks, with zero new inference.
Literal occurrence, semantic support and correctness have separate outcomes;
reviewed support labels cannot be inferred from existing PO gold. Exact-location
mechanics and synthetic controls have their own acceptance gates; real semantic
accuracy requires a separately selected reviewed-anchor study. Workbook parsing
and new representation/model trials remain conditional. The
[execution report](reports/P02-source-provenance.md) records 1,707 selected fields,
explicit ambiguity, unchanged inherited diagnostics and the 1,015-test gate.
The selected inspection capability is concluded, without claiming broader
spreadsheet understanding, semantic accuracy or improved extraction quality.

**Inherited:** row selection/raw fallback and role-cue gains, limited guarded
identifier correction, examples and independent header/line stages. Their
negative results remain concluded; none proves a general workbook parser,
universal local-model limit or all possible staged workflows ineffective.

**New bounded work:** select a genuinely untested representation or support
question. Start with text-span provenance for existing inputs. Neutral workbook
fixtures may exercise sheets, cells, merged headers, leading zeros, dates,
decimals and formula/cached-value semantics; label invented layouts synthetic.
Never invent coordinates lost in the text projection. Reject unsupported
features explicitly and do not execute macros or external links.

Compare source/field support and diagnostic false positives/missed errors before
enabling rejection/correction. Cropping, chunking, pruned stage prompts or new
examples require separately selected experiments with coverage/completeness
controls. No automatic further Gemma tuning or full-corpus rerun is scheduled.

**AI Engineer topics exercised**

| Topics | Project exercise and evidence |
| --- | --- |
| Input Format; System Prompting; Context; Constraints; Structured Output | Compare available structure with current text while preserving authoritative output semantics. |
| Context Sources; Context Evaluation; Context Failure Modes | Retain traceable source references, explicit unknown support, and all intermediate-stage measurements. |
| Zero-Shot; Few-Shot | Instruction-only baseline and inherited example trial; another example package is conditional and separately identified. |
| Manual Implementation; Deterministic Evals; Evaluation Metrics | Evaluate a fixed source-grounded workflow, row/field correctness and diagnostic precision/coverage; deterministic sequencing alone is not agent/tool-calling coverage. |
| Constraining outputs and inputs; Conducting Adversarial Testing | Workbook/text fixtures exercise trust boundaries and bounded parsing/handling. |

**OWASP topics exercised**

| Risk | Bounded P02 exercise |
| --- | --- |
| LLM01 — Prompt Injection | Hostile cell/text content remains untrusted data, with paired legitimate order content. |
| LLM02 — Sensitive Information Disclosure | Only approved neutral sources enter external requests and retained public evidence. |
| LLM03 — Supply Chain | Pin transforms/parser/model/source identities and detect changed representations. |
| LLM05 — Improper Output Handling | Formula-like strings, URLs and markup remain values; outputs cannot become executable workbook operations or commands. |
| LLM09 — Misinformation | Test unsupported rows/codes/dates, missing rows and abstention; support checking must not silently remove legitimate content. |
| LLM10 — Unbounded Consumption | Bound document/archive expansion, dimensions, context, stages, retries and correction loops with controlled fixtures. |

**Acceptance:** inspectable provenance for supported formats; explicit unknown
and unsupported cases; matched comparison and diagnostic error analysis; whole
workflow quality/time/cost, including all stages. Adoption requires predeclared
thresholds; historical outputs and gold remain unchanged.

### P03 — Authorized evidence retrieval and grounded answers

**Question:** Can the system find current, authorized rules/evidence and explain
a field reliably enough to justify the retrieval path?

The [P03 plan](plans/milestones/P03-authorized-retrieval.md) covers
three planned experiments: E01 exact/BM25 baseline, E02 real learned embeddings
with a local Qdrant vector database, and E03 actual LLM-generated cited answers
under matched no-retrieval/BM25/vector contexts. Use a 24-unit schema-derived/
fictional collection and 40 frozen query-context cases. E01 is model-free;
embeddings, vector-store persistence/search/lifecycle and generation are core
planned work, not optional replacements for its advertised topics. Pin actual
encoder/model/store profiles and resource bounds before their live execution;
paid invocations retain the standing concrete-command approval policy.

Fixture scope checks are not production authentication. PO gold, predictions
and P02 diagnostic verdicts stay outside the reference collection. Citation
integrity, retrieval relevance and semantic answer support have separate gates.
Completing E01 alone cannot close P03; completed model-dependent comparisons
may record rejection instead of adoption. The plan includes an
[end-to-end flow](plans/milestones/P03-authorized-retrieval.md#revised-end-to-end-flow).
The planned [I01 integration trial](plans/milestones/P03-authorized-retrieval.md#p03-i01--bounded-langchain-integration-trial)
compares direct Qdrant retrieval/request composition with LangChain using saved
vectors and captured/replayed model outcomes. Application-owned scope, source,
budget and answer checks remain independent. It adds no fourth answer arm or
automatic inference repeat. Keep Qdrant for rd_ai; pgvector remains a candidate
for AspectLoop's separate PostgreSQL-backed retrieval work, subject to its own
plan. This does not change AspectLoop's implementation or select its store.
Remaining stages require their scoped execution gates; this status update starts
no downloads or model invocations.

**E01 executed:** [reference retrieval report](reports/P03-reference-retrieval.md)
records 24 base units, all 40 query-context cases, 12/12 exact positives and
BM25 Recall@3 1.000 / Precision@3 0.431 on authored technical relevance cases.
Irrelevant lexical hits after deletion/revocation remain explicit. The Docker
gate passed 1,041 tests; no new model calls or semantic accuracy claims. Only
S01–S05 was complete at that checkpoint.

**E02 executed:** [vector retrieval report](reports/P03-vector-retrieval.md)
records 58 actual MiniLM encoder batches, real filtered exact Qdrant queries,
update/delete/revocation controls and forty-case recovery after physical restart.
Recall/precision tie BM25; MRR falls to 0.985294, so the +0.05 recall-gain gate
does not support preferring dense retrieval. The store is stopped, data retained.
E03 generation, I01 and final archival remain unexecuted.

**Work:** curate approved field definitions, normalization rules and explicitly
fictional business policies; assign source/chunk/version identities. Establish
deterministic lookup and keyword baselines, then evaluate learned embeddings
with one persistent vector database and actual grounded generation. Hybrid
retrieval/reranking are conditional on a measured
need. Generate cited answers and insufficient-evidence outcomes; test updates,
conflicts, deletion, reindexing and two fictional access scopes. Keep benchmark
answers/predictions out of the evidence collection used for quality claims.

**AI Engineer topics exercised**

| Topics | Project exercise and evidence |
| --- | --- |
| What are Embeddings; Semantic Search; Embedding Models | Measure similarity retrieval against deterministic/keyword controls on reviewed relevance cases. |
| Vector Databases; Purpose and Functionality; Indexing Embeddings; Performing Similarity Search | One selected store/index with reproducible build, version and deletion behavior; no vendor checklist. |
| RAG; Chunking; Embedding; Retrieval Process; Generation; Using SDKs Directly | A small cited-answer pipeline with distinct retrieval and answer scores. |
| RAG Usecases; RAG vs Fine-tuning; RAG & Dynamic Filters; Context Security | Justify retrieval, filter by authority/version before context construction and retain insufficient-evidence behavior. |
| Human Evals; Evaluation Metrics; Cost/latency monitoring | Review relevance, citation support, answer correctness and abstention separately, including operational failures. |
| LangChain / framework integration | Compare real Qdrant-wrapper retrieval and request composition with direct calls; measure parity, overhead and maintenance benefit without claiming agent behavior or improved model accuracy. |

**OWASP topics exercised**

| Risk | Bounded P03 exercise |
| --- | --- |
| LLM01 — Prompt Injection | Retrieved instructions attempt to redirect answers or bypass trusted filters. |
| LLM02 — Sensitive Information Disclosure | Synthetic markers from another principal never enter unauthorized context, output, cache or logs. |
| LLM03 — Supply Chain | Detect changed reference/embedding/index identities and require a reviewed update. |
| LLM04 — Data and Model Poisoning | Introduce/remove a manipulated reference fixture; test approval/reindex lifecycle. Model-training poisoning remains deferred. |
| LLM05 — Improper Output Handling | Treat retrieved links/content and generated citations as data, with safe downstream handling. |
| LLM08 — Vector and Embedding Weaknesses | Test cross-scope similarity, stale chunks, index changes and deletion. |
| LLM09 — Misinformation | Fabricated citations, conflicting rules and unsupported answers require rejection or abstention. |
| LLM10 — Unbounded Consumption | Bound ingestion/chunking, retrieval expansion, context and generation attempts. |

**Acceptance:** reproducible authorized lookup/index behavior, reviewed relevance
and answer/citation cases, update/deletion/isolation controls and full cost/time
populations. A measured decision to retain simpler lookup is valid; embeddings,
vector and generated-answer experiments must actually run to close the planned
P03 scope, even if their candidates are rejected. The bounded I01 integration
trial must also be recorded, without requiring permanent LangChain adoption.
Reranking remains optional;
topic coverage is claimed only for work actually exercised. Unreviewed semantic
quality remains unresolved, not an automatic answer-quality pass.

### P04 — Human-reviewed proposals and bounded orchestration

**Question:** Can the application produce useful, inspectable proposals, and
does model-directed tool use improve them over a fixed workflow?

**Work:** implement typed read-document, retrieve-evidence/rules, validate and
propose operations. Trusted context supplies identity/access scope. Establish
the fixed workflow and structured edit/no-change/abstention results first.
Approval/application are separate human commands with document-version checks;
original extraction remains immutable. Then, if selected, compare one bounded
agent with the same tools/cases and one context strategy. Local MCP exposure
and one client exercise are a separate consumer/learning slice; remote MCP and
multi-agent execution remain conditional extensions.

The [framework comparison](#framework-and-sdk-experiments) places the proposed
Python LangGraph trial here, after the fixed workflow. Compare orchestration
without changing model behavior first; a graph containing deterministic steps
does not demonstrate model-directed agency. LangChain integration and LangSmith
tracing are independently selected candidates, not required companion products.

**AI Engineer topics exercised**

| Topics | Project exercise and evidence |
| --- | --- |
| Tools & Function Calling; Function Calling | Typed requests/results validated independently of the model; proposals grant no permission. |
| Agents Usecases; AI Agents; Manual Implementation | Conditional manual versus LangGraph orchestration comparison, followed by a separately selected model-directed-loop comparison; retain total quality, calls and latency and claim only exercised behavior. |
| Context Window; Context Compaction; Context Isolation; State & Historical Context; Memory Systems | Compare bounded policies; test lost constraints, stale state and cross-document/session contamination. |
| MCP Host; MCP Client; MCP Server; Data Layer; Transport Layer; Connect to Local Server | Conditional local MCP slice reuses domain tools; record actual client/transport behavior. |
| LLM Evaluations; Tracing & logging; Cost/latency monitoring | Task/no-change/abstention scores and tool/evidence traces, including interrupted or repeated calls. |

**OWASP topics exercised**

| Risk | Bounded P04 exercise |
| --- | --- |
| LLM01 — Prompt Injection | Document, reference and tool-result payloads attempt unauthorized behavior. |
| LLM02 — Sensitive Information Disclosure | Trusted scope, tool results and context/memory preserve principal/document isolation. |
| LLM05 — Improper Output Handling | Malformed tool arguments/results and hostile proposal values fail independent validation. |
| LLM06 — Excessive Agency | Deny unrestricted file/network access, direct submission/mutation and stale/unauthorized apply; verify legitimate approved apply separately. |
| LLM07 — System Prompt Leakage | Prompt disclosure/role text cannot grant tool authority or bypass human approval. |
| LLM09 — Misinformation | Unsupported/unnecessary edits and false no-change decisions are scored against reviewed cases. |
| LLM10 — Unbounded Consumption | Bound steps, retries, calls, tokens, time and spend; retain interrupted and unknown-charge outcomes. |

**Acceptance:** useful reviewed proposals, rejected stale/unauthorized actions,
independently tested tools and complete task/operational evidence. Agent/context/
MCP experiments have explicit separate outcomes; unselected mechanisms are not
required for fixed-workflow acceptance or counted as completed topics.

### P05 — Local interface, operations and quality release loop

**Question:** Can a selected useful workflow operate predictably, and can a
version change be accepted or rolled back using evidence?

**Work:** expose one workflow through a small API/CLI and minimal review
interaction, reusing domain behavior. Exercise local authentication/document
authorization, cancellation/concurrency/duplicate-request handling, dependency
failure and durable accounting. Compare one useful optimization with quality
and access/version-aware cache controls. Streaming is conditional. Correlate
bounded logs/metrics/traces; define code/prompt/model/schema/reference/index/eval
release identities and demonstrate candidate rejection/rollback. Feedback is
draft labeling material until reviewed; no automatic training-data promotion.

Assess a selected LangSmith pilot against the
[framework/SDK criteria](#framework-and-sdk-experiments), including redaction,
export/retention controls, trace-to-run correlation and telemetry outage behavior.
Hosted tracing is optional; saved evidence and accounting remain usable without
it. Preserve the independent AspectLoop telemetry decision.

**AI Engineer topics exercised**

| Topics | Project exercise and evidence |
| --- | --- |
| OpenAI-compatible APIs; Using SDKs Directly | Preserve existing provider boundaries while exposing the application workflow; another SDK is not required. |
| Streaming Responses; Prompt Caching | Conditional exercises only when selected; partial text is not a validated final result, and application response caching alone is not prompt caching. |
| LLM Observability; Tracing & logging; Cost/latency monitoring | Correlate requests, tool/retrieval work, cancellations, known/unknown charges and measured workload behavior; a conditional LangSmith pilot must meet the same evidence/privacy boundaries. |
| Production monitoring; Regression Testing | Exercise local quality gates, versioned release/feedback handling and rollback; local tests do not establish production deployment readiness. |
| Security and Privacy Concerns; Constraining outputs and inputs; Conducting Adversarial Testing | Verify the end-to-end interface's permission, handling and resource boundaries. |

**OWASP topics exercised**

| Risk | Bounded P05 exercise |
| --- | --- |
| LLM01 — Prompt Injection | Retain prior boundary/quality cases through the exposed workflow; avoid claiming prompt-only prevention. |
| LLM02 — Sensitive Information Disclosure | Authenticated document access, redacted correlated evidence and principal-aware cache isolation. |
| LLM03 — Supply Chain | Bind release inputs and demonstrate rejection/rollback of an unaccepted artifact update. |
| LLM04 — Data and Model Poisoning | Feedback/reference candidates require review and versioning before labels or indexes change. |
| LLM05 — Improper Output Handling | Safe API/rendered/exported values; partial streams and proposals cannot masquerade as validated final results. |
| LLM06 — Excessive Agency | API/tool entrypoints retain trusted authorization and explicit human apply checks. |
| LLM08 — Vector and Embedding Weaknesses | Where retrieval exists, invalidate stale/access-incompatible cached/indexed evidence. |
| LLM09 — Misinformation | Slice-aware quality regressions and reviewed feedback; no silent acceptance of model-generated labels. |
| LLM10 — Unbounded Consumption | Workload bounds, cancellation, concurrency, duplicate handling and durable unresolved accounting. |

**Acceptance:** repeatable bounded workload, authorization/cache/cancellation
failure controls, correlated evidence and a demonstrated quality rejection and
rollback. Report local/controlled tests separately from any approved live
observations. A large frontend, identity platform, hosted telemetry subscription
or production deployment is not a prerequisite.

## 6. OWASP coverage register

The milestone tables define actual scope; this index makes omissions visible.
All mappings start as planned or inherited-limited, never automatically mitigated.
Record any deferred sub-risk rather than claiming the whole category covered.

| OWASP 2025 risk | Initial exercise | Later extension |
| --- | --- | --- |
| LLM01 Prompt Injection | P01 | P02–P05 document/retrieval/tool/API paths |
| LLM02 Sensitive Information Disclosure | P00 preservation checks; P01 context cases | P02–P05 source, principal, cache and log paths |
| LLM03 Supply Chain | P00 inherited identity checks/migration | P02/P03 transforms/references; P05 releases |
| LLM04 Data and Model Poisoning | P03 reference fixtures | P05 feedback; training-time poisoning deferred |
| LLM05 Improper Output Handling | P01 controlled downstream cases | P02–P05 parsers, tools, API and rendering |
| LLM06 Excessive Agency | P04 | P05 exposed approval/authority boundaries |
| LLM07 System Prompt Leakage | P01 | P04 prompt/tool authority separation |
| LLM08 Vector and Embedding Weaknesses | P03 | P05 index/cache lifecycle |
| LLM09 Misinformation | P00 measurement/claim preservation; P01 quality cases | P02–P05 support, citations, proposals and regressions |
| LLM10 Unbounded Consumption | P00 inherited-bound preservation; P01 fixtures | P02–P05 parsing, retrieval, loops and workload controls |

For each case retain asset/trust boundary, attacker-controlled input/access,
expected prohibited outcome, positive control, configuration and observations,
mitigation, residual risk and evidence link. Category mapping alone is not a test.
Relevant primary guidance includes
[prompt injection](https://genai.owasp.org/llmrisk/llm01-prompt-injection/),
[excessive agency](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/)
and [system prompt leakage](https://genai.owasp.org/llmrisk/llm072025-system-prompt-leakage/).

## 7. Conditional extensions and completion decisions

| Extension / AI Engineer topics | Trigger and boundary |
| --- | --- |
| PDF ingestion; Image Understanding; Multimodal AI | Representative authorized documents or a named visual failure; synthetic neutral workbook renders do not prove real PDF/scan capability. |
| Fine-tuning; additional Self-Hosted Models; Inference Engineering | Reviewed data or a named quality/latency/memory hypothesis; preserve source groups and compare total workflow cost. No model leaderboard or training program by default. |
| Model-Based Evals / JEV routing | Reviewed rubric and a calibrated verifier study first; a live cascade needs a separate cost/quality case and approval. |
| Multi-agents; Multi-agent Context Sharing | A demonstrated single-workflow limitation; compare delegation cost and authority against the simpler baseline. |
| Connect to Remote Server / remote MCP; deployment | A real consumer and a separate authorization/transport/operational slice. |
| Data Classification; Anomaly Detection; Recommendation Systems | A useful bounded task with its own labels/metrics; not required to expand curriculum coverage. |

Audio/video generation, foundation-model training, GPU clusters, Kubernetes and
multiple interchangeable orchestration/telemetry stacks remain outside current
core scope. No topic coverage is claimed merely because a coding assistant is
used during implementation.

Milestone plans record work and status; guides/reference describe accepted
behavior; reports retain observations, identities and limits. Keep the roadmap
compact enough to identify current decisions rather than accumulating the
historical implementation plan's interleaved execution diary.

The original P00 root migration and low-risk cleanup are concluded. The S08
follow-up migrates live settings, package metadata and Compose project naming,
with independent preservation gates. Persistent-data and archive-format names
remain unchanged.
Select later P01/capability slices from actual gaps and available data;
model experiments are not automatically scheduled.
All billable model, embedding or judge invocations need the concrete scope,
allowance and standing human approval; roadmap creation grants none.

## 8. Revision history

| Version | Date | Change |
| --- | --- | --- |
| 1.0 | 2026-10-31 | First versioned project roadmap: completed 240-observation/sections 8–9 baseline, inherited local trials, P00 root consolidation, per-milestone AI Engineer and OWASP mappings. |
| 1.1 | 2026-10-31 | P00 executed: root application, command compatibility, preserved artifacts/storage and verified isolated reproduction. |
| 1.2 | 2026-10-31 | Add planned P00-S08 legacy-name cleanup/risk review; retain concluded root migration and immutable evidence. |
| 1.3 | 2026-10-31 | Retire aliases/current legacy command instructions; retain sensitive identities and historical evidence. |
| 1.4 | 2026-10-31 | Select DI settings, package metadata and disposable Compose naming; retain persistent storage and archive identities. |
| 1.5 | 2026-10-31 | Add draft P01 implementation plan: offline protocol/exposure/rubric work, paired comparisons, bounded challenges and conditional judge calibration. |
| 1.6 | 2026-11-01 | Conclude P01 offline protocol/comparison scope with 982-test gate, finite controls, preserved baseline and verified archival; human/judge/live-model extensions unexercised. |
| 1.7 | 2026-11-07 | Place conditional LangChain/LangGraph comparisons in P03/P04 and LangSmith assessment in P04/P05; retain Python baseline, independent AspectLoop AI SDK proposal, accounting/authority boundaries and explicit adoption/export gates. |
| 1.8 | 2026-11-07 | Add draft P02-E01 text-provenance implementation plan; distinguish inherited diagnostics, exact locations, semantic review authority and conditional workbook/model experiments. |
| 1.9 | 2026-11-07 | Execute selected P02 text-provenance slice without inference: bound locations and inherited context linkage, offline commands, preserved P01/matrix results and 1,015-test gate; broader workbook/semantic studies remain conditional. |
| 1.10 | 2026-11-07 | Verify P03 boundaries and add draft offline authorized-reference retrieval plan; separate exact/lexical baselines, technical relevance labels, lifecycle/access controls and evidence excerpts from conditional embeddings and generated RAG answers. |
| 1.11 | 2026-11-08 | Revise P03 to require planned real embeddings, local Qdrant vector-database operations and actual generated RAG comparisons after the lexical baseline; preserve concrete model/run gates and separate execution, quality and adoption outcomes. |
| 1.12 | 2026-11-08 | Select P03-I01 bounded direct-versus-LangChain Qdrant retrieval/composition trial with application-owned controls and replay parity; preserve Qdrant for rd_ai and pgvector as a separate AspectLoop candidate. |
| 1.13 | 2026-11-08 | Record executed S01–S05/E01 and its 1,041-test gate, technical-fixture relevance results and lexical insufficiency limits; retain later P03 model/database/integration work and archival as unexecuted. |
| 1.14 | 2026-11-08 | Record real S06/E02 embeddings/Qdrant lifecycle and restart recovery; retain lexical baseline after no recall gain, and keep generation/LangChain/final archival unexecuted. |

Use Git history for prior revisions. Record material changes to milestone scope,
data authority or topic sources here; do not rewrite historical experiment claims.
