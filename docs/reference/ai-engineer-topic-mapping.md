# AI Engineer topics across rd_ai and AspectLoop

- Version: **1.0**.
- Created: **2026-11-07**.
- Research and repository observations: **2026-11-06**.
- Purpose: retain the cross-project learning/capability mapping from discussion.
- Status: reference analysis; not implementation approval or a completion audit.

## Sources and interpretation

External sources checked during the analysis:

- [AI Engineer roadmap](https://roadmap.sh/ai-engineer).
- [Publisher's AI Engineer topic index](https://github.com/nilbuild/developer-roadmap/tree/master/roadmaps/ai-engineer/content).

The topic index contains duplicate/historical names and vendor alternatives;
its file count is not a count of distinct current visual roadmap nodes. Related
topics are grouped here. The upstream links are mutable; this document records
the dated analysis rather than promising continual synchronization.

Project sources:

- [rd_ai roadmap](../roadmap.md), including its inherited evidence and P00–P05
  milestone scope.
- [P01 execution report](../reports/P01-evaluation-protocols.md).
- AspectLoop's canonical `docs/general-plan.md` and
  `docs/agent-model-conventions.md` in the separate AspectLoop repository.

Together, the projects can exercise most application-level AI engineering
topics. Their strongest roles are complementary:

- **rd_ai:** controlled experiments, model comparisons, evaluation, source
  grounding and retrieval.
- **AspectLoop:** authenticated workflows, reviewer interaction, tools,
  asynchronous processing, observability and deployment.

Legend:

- **E:** exercised within the recorded scope; not mastery or general reliability.
- **P:** planned, not completed.
- **C:** possible conditional extension; not necessarily selected or approved.
- **—:** outside the current scope.

An existing software foundation is not automatically completed AI coverage.
For example, application logs do not establish LLM tracing, Socket.IO events
do not establish token streaming, and using a coding agent does not implement
an agent inside either application. This reference does not change either
project's canonical scope, dependencies or live-inference permissions.

## Topics that fit the projects

| Roadmap topic family | rd_ai | AspectLoop | Useful way to exercise it |
| --- | --- | --- | --- |
| AI engineer roles, use cases, product impact | **E:** experiment decisions and limits | **P:** document-processing product | Record when AI adds value, when deterministic processing suffices, and what review effort remains. |
| LLM fundamentals, pretrained models, model types | **E:** inference experiments and P01 explanations | **P:** AI00 foundation | Connect token/context/output behavior to actual failures. Understanding model training does not require training one. |
| Choosing models; open/closed models | **E:** Gemma, Qwen and provider comparisons | **P:** AI30 | Compare complete-workflow quality, latency, cost and reviewer effort using the same cases. |
| Hosted APIs, OpenAI-compatible APIs, OpenRouter | **E:** provider and Ollama adapters | **P:** AI10/AI30 | Exercise authentication, structured responses, errors, usage reporting and provider differences behind adapters. |
| Using SDKs directly | **C:** existing adapters use HTTP directly | **P/C:** provider integration | Implement one native SDK adapter only if its behavior or capabilities warrant comparison. HTTP integration alone is not SDK coverage. |
| Self-hosted models; Ollama | **E:** native local inference | **C:** optional provider implementation | Connect a fixed local model through the same product contract and measure its operational limitations. |
| Hugging Face Hub/models/tasks/inference SDK | **C** | **C** | Pin and evaluate one relevant model or embedding artifact. Using an Ollama model does not automatically exercise Hub workflows. |
| Prompt engineering: roles, system instructions, input format, constraints | **E:** versioned prompts and representations | **P:** AI10/AI11 | Compare one changed instruction or representation against a frozen baseline. |
| Zero-shot and few-shot prompting | **E:** instruction-only and example trials | **P/C:** extraction and correction prompts | Measure gains and regressions; disclose which examples informed development. |
| Tokens, context window and long-context processing | **E:** admission/context/output experiments | **P:** AI11 | Preserve document completeness while measuring truncation, context admission, token use and latency. |
| Temperature, top_p and sampling parameters | **E:** controlled sampling experiments | **P:** AI30 | Compare fixed profiles without mixing prompt/model changes into the conclusion. |
| Top-k and repetition penalties | **C:** where the selected runtime supports them | **C** | Run a bounded diagnostic only for a specific repetition problem. Do not assume equivalent controls exist across providers. |
| Structured output and input/output constraints | **E:** authoritative schema and validation | **P:** AI00/AI10 | Test wrong-but-valid values alongside malformed output; structural validity and factual correctness need separate metrics. |
| Context engineering, sources and failure modes | **E:** representation/support trials; **P:** P02 | **P:** AI11/AI21 | Assemble bounded source/rule context and measure missing evidence, irrelevant context and lost constraints. |
| State, historical context, external memory | **C:** P04 | **P/C:** correction assistant | Retain document/session state with explicit version and access scope. Keep business state distinct from model conversation history. |
| Context compaction | **C:** P04 | **C:** AI21 | Compare full history with compacted history; test whether important constraints or unresolved issues disappear. |
| Context isolation and security | **E:** limited controls; **P:** P03–P05 | **P:** assistant and authorization integration | Use two fictional users/documents and verify that another document's evidence never enters unauthorized context. |
| Embeddings, embedding models and semantic search | **P:** P03 | **C:** correction-rule retrieval | Compare keyword lookup with embeddings on reviewed relevance cases. |
| Vector databases, indexing and similarity search | **P:** P03 | **C:** assistant retrieval | Use one store; test updates, deletion, versioning and access filters, not just successful similarity queries. |
| RAG: chunking, embedding, retrieval and generation | **P:** P03 | **C:** AI20/AI21 | Answer field questions using cited schema/rule/source evidence and explicit insufficient-evidence outcomes. |
| RAG dynamic filters; RAG versus fine-tuning | **P:** P03 | **C:** document/customer-scoped rules | Filter by authorized scope and rule version; establish whether retrieval solves the actual problem before considering training. |
| Deterministic evaluations and evaluation metrics | **E:** scorer, paired reports and controls | **P:** AI00 | Reuse the evaluation principles for product contracts, preserving failures and complete populations. |
| Human evaluations | **E:** original approved gold; further review conditional | **P:** reviewer workflow | Review disagreements, unsupported edits, no-change decisions and review time. UI clicks alone do not establish factual correctness. |
| Model-based evaluations | **C:** P01 judge study unselected | **C:** AI30 | Calibrate against reviewed anchors; measure false acceptance and disagreement before using a judge's verdict. |
| Regression testing | **E:** implementation and saved-result checks | **E:** general software gates; **P:** AI regressions | Reject code/prompt/model/reference changes that breach declared quality or operational thresholds. |
| Tools and function calling | **C:** P04 | **P:** AI20 | Expose typed read/proposal/validation tools. Validate arguments and permissions independently of the model. |
| Agents, agent use cases, manual implementation | **C:** P04 | **P:** AI21 | Compare a fixed workflow with one bounded model-directed loop on identical tasks. Keep the agent only if it improves the outcome. |
| ReAct-style orchestration | **C** | **C:** AI21 | Observe action → tool result → next action with step limits and auditable tool traces. No private reasoning disclosure is needed. |
| MCP host/client/server, data and transport layers | **C:** P04 local MCP slice | **P/C:** AI20 | Expose existing domain tools through one local MCP server and exercise a real client. Domain tools remain usable without MCP. |
| Remote MCP | **C:** separate extension | **C:** authenticated tool access | Add remote transport, authentication, scope checks and cancellation only after local tools are useful. |
| Streaming responses | **C:** P05 | **C:** assistant UX | Stream explanations or progress while keeping incomplete output distinct from a validated final proposal. Socket.IO status events alone are not model-token streaming. |
| Prompt caching | **C:** P05 | **C:** AI30 | Measure supported provider prefix caching with repeated schema/rule context. Keep it distinct from application response caching. |
| Cost/latency monitoring | **E:** request accounting and measured populations | **P:** AI30 | Measure retries, failures, all stages and review effort; retain unknown charges rather than treating them as free. |
| Tracing, logging and LLM observability | **E:** saved execution evidence; **P:** P05 correlation | **E:** logging foundation; **P:** M10/AI30 | Trace a document through queue, retrieval, model calls, validation and reviewer decision with redacted metadata. |
| Production monitoring | **C:** beyond local P05 evidence | **P:** M10/M11/AI30 | Exercise drift, dependency failures, alerts and rollback under a deployed workload. Local test success is not production evidence. |
| Prompt injection, privacy, constrained behavior and adversarial testing | **E:** bounded technical controls; broader tests planned | **P:** M10 and AI tracks | Test hostile documents, retrieved text and tool results with legitimate positive controls. Measure model behavior separately from enforced application authority. |
| AI safety, ethics, customer understanding | **E:** disclosure and authority boundaries | **P:** reviewer-centered product | Make unsupported answers visible, preserve originals, require approval for consequential changes and document deployment limitations. |

## Topics requiring a scope decision

These are not automatically impossible. Some are reasonable document-workflow
extensions; others are more honestly covered in a separate learning exercise.

| Topic | Fit in rd_ai / AspectLoop | Why conditional or outside scope | Possible exercise |
| --- | --- | --- | --- |
| Image understanding / vision | **C** / **P: AI12** | Current rd_ai evidence is text-based; AspectLoop is PDF-first. | Compare extracted PDF text with page images on neutral scans, keeping page provenance and reviewed labels. |
| Multimodal AI | **C** / **P/C: AI12** | Useful when document text alone loses important layout or visual evidence. | Combine text, page image and structured fields; measure additional benefit and cost. |
| Audio, speech-to-text, text-to-speech, Whisper | **—** / **C** | Neither current workflow consumes audio. | A voice-assisted review or accessibility feature could justify it; otherwise use a separate audio exercise. |
| Video understanding | **—** / **—** | Neither project has a video-processing requirement. | Use a separate video task rather than attaching video to PO extraction for coverage. |
| Image generation; DALL·E/Nano Banana APIs | **C:** test assets / **C:** design assets | Generation is not needed for extraction or correction correctness. | Create synthetic visual fixtures or UI assets with explicit truth checking. Keep aesthetic generation outside extraction-quality claims. |
| Data classification | **C** / **C** | The initial workflow targets one document type. | Add reviewed document-type routing or sensitivity classification with an explicit unknown class. |
| Anomaly detection | **C** / **C** | Requires a definition of an actionable anomaly. | Compare rules and statistical outlier ranking for suspicious quantities/prices; measure false alerts and review burden. |
| Recommendation systems | **Weak fit** / **Weak fit** | There is no established user–item preference/history problem. | Review prioritization or suggestion ranking is possible, but is not a full personalized recommender. Use a separate dataset for that topic. |
| Bias and fairness | **C** / **C** | Can be studied, but gold10 cannot support broad fairness conclusions. | Measure error and abstention differences across reviewed language/layout/scan-quality groups. Do not invent demographic claims from supplier documents. |
| Fine-tuning | **C:** separate study / **deferred** | Existing labels are too limited and repeatedly reused for a credible training/generalization study. | Assemble a larger reviewed, grouped dataset, then compare a small adaptation against the unchanged baseline and an independent evaluation set. |
| Training models from scratch | **Outside core scope** / **outside core scope** | Both projects apply pretrained models; foundation training is a different engineering problem. | Use a separate small educational training exercise. The roadmap distinguishes AI application engineering from building models from scratch. |
| Inference engineering / advanced GPU serving | **C** / **deferred** | Native Ollama covers only part of serving engineering; distributed serving needs another workload and hardware case. | Benchmark batching, concurrency, quantization and memory on a fixed model. Expand infrastructure only when the experiment warrants it. |
| Multi-agent systems and shared context | **C** / **C** | No demonstrated need for several agents yet. | Compare a single controller with a bounded extractor/critic arrangement; include total cost, conflicting decisions and shared-context leakage. |
| AI versus AGI | **Conceptual only** / **conceptual only** | A document workflow cannot experimentally demonstrate AGI. | Explain the distinction through the projects' bounded capabilities and failure modes. |

## Tools and vendors are alternatives

Adopting each named tool would add maintenance without necessarily adding
learning. A bounded comparison or justified adoption counts more than installation.
Capabilities, compatibility and pricing need verification when a trial is selected.

| Roadmap tool families | Where a trial fits | Useful exercise |
| --- | --- | --- |
| OpenAI, Claude, Gemini, Cohere; Llama, Gemma, Qwen, Mistral, DeepSeek | rd_ai model comparison; AspectLoop provider adapters | One deliberately selected comparison with matched cases and complete costs. Existing Gemini use through OpenRouter does not exercise every native provider API. |
| Ollama, LM Studio, Hugging Face serving | Primarily rd_ai | Compare one runtime behavior or deployment constraint. Installing another launcher alone adds little evidence. |
| FAISS, Chroma, Qdrant, Pinecone, Weaviate, LanceDB, MongoDB Atlas, Supabase | P03 retrieval experiment | Choose one index/store and verify retrieval quality, filtering and lifecycle. They are not interchangeable in every capability. |
| LangChain, LlamaIndex, Haystack, RAGFlow, Modus; agent SDKs/ADK/Agent Builder | Optional R&D branches | Compare one framework-assisted workflow with the existing manual implementation; measure value and added complexity. |
| DeepEval, Ragas | Evaluation extension | Check whether a selected metric detects failures that the current evaluator misses, using reviewed anchors. |
| Langfuse, LangSmith, Arize, Helicone, PostHog | R&D evaluation or product operations pilot | Address a concrete visibility gap. Preserve AspectLoop's selected telemetry boundaries rather than installing parallel stacks indiscriminately. |
| DataHub, Atlan | Low-priority governance extension | Demonstrate lineage/version/access questions that manifests and artifact metadata cannot reasonably answer. Current scale may not justify a catalog platform. |
| Codex, Claude Code, Cursor, Windsurf, OpenCode, Replit, Devin | Development workflow in either repository | Compare changes, review quality and verification discipline. Their use does not count as product function calling, MCP or multi-agent capability. |
| Transformers.js | Conditional browser experiment | Run a small local classification or embedding task if browser privacy/latency provides a concrete advantage. It is not a prerequisite for the current Python/TypeScript architectures. |

## Suggested division and sequence

Prove uncertain AI behavior in rd_ai, then bring selected capabilities into
AspectLoop through its own contracts and acceptance gates. Code or runtime
reuse is a separate architecture decision; an rd_ai experiment does not require
AspectLoop to adopt Python or bypass its mocked end-to-end foundation.

The strongest remaining sequence is:

1. Source provenance and inspectable support judgments.
2. Authorized retrieval with separate retrieval and answer evaluation.
3. Typed correction tools with explicit human authority.
4. A bounded assistant comparison against the fixed workflow.
5. Product observability, operational controls and deployment.

Audio, video, foundation training and broad vendor coverage can remain separate
exercises unless a real requirement emerges. No additional customer documents
are assumed available. Synthetic fixtures and new reviewed labels on existing
inputs can support declared development experiments, but neither creates an
independent holdout after prior exposure.

No implementation, model download, inference, paid call, new label approval or
cross-repository change is authorized by this reference document.

## Revision history

| Version | Date | Change |
| --- | --- | --- |
| 1.0 | 2026-11-07 | Preserve the 2026-11-06 cross-project topic mapping, current/planned/conditional distinctions, scope gaps and possible exercises. |
