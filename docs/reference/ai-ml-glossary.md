<a id="glossary-top"></a>

# Living AI/ML engineering glossary

- Version: **1.4**.
- Created and terminology reviewed: **2026-11-07**.
- Scope: AI Engineer roadmap concepts, practical ML/LLM engineering and interview preparation.
- Owner: maintain with relevant work in rd_ai and AspectLoop; Elemica remains a read-only reference.

This is a learning reference, not a claim that every technique is implemented.
Definitions are original summaries; primary sources and project evidence are
listed below. Interview cues are practice prompts, not a survey of employers or
a guarantee of interview frequency. Product names are examples, not endorsements.
Changing capabilities, prices, model limits and protocol versions require a
fresh check when used; this glossary deliberately avoids a model leaderboard.

## How to use and maintain it

[Back to top](#glossary-top) · [Term index](#term-index) · [Project evidence](#project-evidence) · [Sources](#primary-sources)

Use the [alphabetical term index](#term-index) or click an ID to jump. Each term
has a stable anchor; do not renumber existing IDs when adding terms. Read the definition, connect it to evidence, then explain the
interview distinction in your own words. Acronyms are expanded at first use.

Example labels:

- **Observed:** code or recorded project evidence supports the bounded example.
- **Documented reference:** inspected local enterprise documentation/code;
  execution, deployment and production outcomes were not verified here.
- **Planned:** belongs to a project plan, not completed coverage.
- **Hypothetical:** an illustrative exercise, not implemented behavior.
- **Conceptual:** useful knowledge with no implementation claim.

After relevant project work, update affected entries with evidence and status.
Add a term when it explains a real decision, failure, experiment or interview
discussion. Update counterexamples when results invalidate an earlier intuition.
Do not churn the glossary for unrelated edits or change historical measurements.
Use the [maintenance procedure](#maintenance-procedure) and the project guidance.

Contents (or use the [alphabetical term index](#term-index)):

1. [Foundations and roles](#foundations-and-roles)
2. [Training and adaptation](#training-and-adaptation)
3. [Data and generalization](#data-and-generalization)
4. [Tokens, prompting and generation](#tokens-prompting-and-generation)
5. [Documents, grounding and decisions](#documents-grounding-and-decisions)
6. [Evaluation and statistics](#evaluation-and-statistics)
7. [Retrieval and RAG](#retrieval-and-rag)
8. [Agents, tools and context](#agents-tools-and-context)
9. [Serving, operations and system design](#serving-operations-and-system-design)
10. [Safety and security](#safety-and-security)
11. [Project evidence](#project-evidence)
12. [LangChain, LangGraph and LangSmith](#langchain-langgraph-and-langsmith)
13. [Interview practice](#interview-practice)
14. [Primary sources](#primary-sources)
15. [Maintenance procedure](#maintenance-procedure)

## Term index

[Back to top](#glossary-top) · [Project evidence](#project-evidence) · [Sources](#primary-sources)

Choose a term or alias to jump directly to its definition. IDs stay stable when wording changes.

**A:** [A/B release](#term-o16) · [A2A](#term-agen15) · [Ablation](#term-v11) · [Abstention](#term-x09) · [Accuracy](#term-v06) · [Agent](#term-agen02) · [Agent framework](#term-agen18) · [AI engineering](#term-f01) · [Alignment](#term-t15) · [alignment](#term-v09) · [ANN](#term-rag08) · [Annotation versus approval](#term-d04) · [artifact](#term-o14) · [attention](#term-f07) · [augmentation](#term-d13) · [Authentication versus authorization](#term-sfty01) · [authorized retrieval](#term-rag12)

**B:** [backpressure](#term-o04) · [backpropagation](#term-t05) · [baseline](#term-v01) · [Batch](#term-t07) · [Batching](#term-o04) · [benchmark](#term-v01) · [Bi-encoder](#term-rag10) · [BM25](#term-rag04)

**C:** [calibration](#term-x08) · [canary](#term-o16) · [cancellation](#term-o06) · [capability boundary](#term-agen16) · [Chain of thought](#term-g11) · [Chunking](#term-rag06) · [Circuit breaker](#term-o08) · [Citation](#term-x05) · [citation correctness](#term-rag15) · [Class imbalance](#term-d12) · [Classification](#term-f11) · [client](#term-agen12) · [concept drift](#term-d10) · [concurrency](#term-o04) · [Confidence](#term-x08) · [confidence interval](#term-v13) · [constrained decoding](#term-g12) · [contamination](#term-d07) · [Context compaction](#term-g14) · [Context engineering](#term-g13) · [Context isolation](#term-agen09) · [Context window](#term-g02) · [controlled experiment](#term-v11) · [corpus](#term-d01) · [correction overlay](#term-x12) · [correlation ID](#term-o12) · [Cosine](#term-rag05) · [Coverage](#term-v15) · [CPU/GPU acceleration](#term-o05) · [cross-encoder reranking](#term-rag10)

**D:** [DAG](#term-agen01) · [Data drift](#term-d10) · [Data lineage](#term-d14) · [Data/model poisoning](#term-sfty08) · [database](#term-rag07) · [Dataset](#term-d01) · [Dataset versioning](#term-d15) · [deadline](#term-o06) · [decode](#term-o01) · [Decoding](#term-g05) · [deduplication](#term-o09) · [deep learning](#term-f03) · [Dense model](#term-f09) · [Dense versus sparse retrieval](#term-rag03) · [dependency stop](#term-o08) · [Deterministic, human and model-based evals](#term-v03) · [Development set](#term-v12) · [Direct/indirect prompt injection](#term-sfty03) · [distance](#term-rag05) · [Distillation](#term-t12) · [distribution shift](#term-d09) · [DLQ](#term-o10) · [dot product](#term-rag05) · [DPO](#term-t14)

**E:** [Embedding](#term-rag02) · [epoch](#term-t07) · [error budget](#term-o15) · [Evaluation](#term-v01) · [exact match](#term-v06) · [Excessive agency](#term-sfty05) · [exfiltration](#term-sfty04) · [Experiment tracking](#term-o14) · [exponential backoff](#term-o07) · [Exposure history](#term-d08) · [Extraction versus normalization](#term-x03)

**F:** [F1](#term-v05) · [Faithfulness](#term-rag15) · [fallback](#term-agen17) · [false acceptance](#term-v14) · [Feature](#term-d02) · [Feature store](#term-d16) · [few-shot](#term-g10) · [Fine-tuning](#term-t10) · [finish reason](#term-g15) · [FN](#term-v04) · [Foundation model](#term-f05) · [FP](#term-v04) · [function calling](#term-agen04)

**G:** [Generalization](#term-d09) · [Generative AI](#term-f04) · [gold](#term-d03) · [Gradient](#term-t05) · [ground truth](#term-d03) · [Grounding](#term-x04) · [grouped split](#term-d06)

**H:** [Hallucination](#term-x06) · [Harness](#term-agen03) · [history](#term-agen08) · [HNSW](#term-rag08) · [Holdout](#term-d06) · [Human in the loop](#term-x10) · [Hybrid search](#term-rag09) · [Hyperparameter](#term-t08)

**I:** [Idempotency](#term-o09) · [Immutable baseline](#term-x12) · [Improper output handling](#term-sfty06) · [In-context learning](#term-t17) · [independent evaluation](#term-v12) · [Index lifecycle](#term-rag16) · [instruction resource](#term-agen10) · [inter-token latency](#term-o03)

**J:** [jitter](#term-o07) · [Judge calibration](#term-v14)

**K:** [Known cost](#term-v20) · [KV cache](#term-o02)

**L:** [Label](#term-d03) · [LangChain](#term-agen19) · [LangGraph](#term-agen20) · [LangSmith](#term-o19) · [Latency percentile](#term-v19) · [Layout/table understanding](#term-x02) · [Leakage](#term-d07) · [learning rate](#term-t06) · [least privilege](#term-sfty02) · [lineage](#term-o14) · [LLM](#term-f06) · [LLMOps](#term-o18) · [Logits](#term-g04) · [logs](#term-o13) · [LoRA](#term-t11) · [Loss function](#term-t04)

**M:** [Machine learning](#term-f03) · [macro aggregation](#term-v07) · [MCP](#term-agen11) · [MCP host](#term-agen12) · [MCP tools](#term-agen13) · [Memory](#term-agen08) · [Metadata filtering](#term-rag12) · [Metrics](#term-o13) · [Micro](#term-v07) · [minimization](#term-sfty11) · [mixture of experts (MoE)](#term-f09) · [ML engineering](#term-f02) · [MLOps](#term-o18) · [model provenance](#term-sfty12) · [model registry](#term-d16) · [MRR](#term-rag14) · [Multi-agent system](#term-agen07) · [Multimodal model](#term-f12)

**N:** [nDCG](#term-rag14)

**O:** [observability](#term-o13) · [OCR versus text extraction](#term-x01) · [Offline eval](#term-v18) · [offload](#term-o05) · [online experiment](#term-v18) · [Optimistic concurrency](#term-o11) · [Optimizer](#term-t06) · [orchestrator-workers](#term-agen06) · [outbox](#term-o10) · [output allowance](#term-g03) · [Overfitting](#term-t18) · [overlap](#term-rag06)

**P:** [Paired comparison](#term-v10) · [Parameters](#term-f08) · [PEFT](#term-t11) · [Perplexity](#term-v16) · [PII](#term-sfty11) · [pipeline](#term-agen01) · [Planner/executor](#term-agen06) · [population](#term-v19) · [Positional matching](#term-v09) · [Precision](#term-v05) · [precision@k](#term-rag13) · [Prefill](#term-o01) · [Present/null populations](#term-v08) · [pretrained model](#term-f05) · [Pretraining](#term-t09) · [Prompt budget](#term-g03) · [Prompt caching](#term-g17) · [Prompt engineering](#term-g08) · [Prompt injection](#term-g16) · [Prompt/model/schema version](#term-g18) · [prompts](#term-agen13) · [Proposal versus application](#term-x11) · [protocol](#term-agen14) · [provenance](#term-d14) · [provenance span](#term-x05)

**Q:** [Quantization](#term-t16) · [Query rewriting](#term-rag11) · [Queue](#term-o10)

**R:** [RAG](#term-rag01) · [RAG versus fine-tuning](#term-rag17) · [ReAct](#term-agen05) · [reasoning model](#term-g11) · [recall](#term-v05) · [Recall@k](#term-rag13) · [regression](#term-f11) · [regression](#term-v10) · [Reinforcement learning](#term-t13) · [Release identity](#term-o17) · [Repetition penalty](#term-g07) · [representation](#term-d02) · [reproducibility](#term-d15) · [reservation](#term-v20) · [resources](#term-agen13) · [response caching](#term-g17) · [retention](#term-sfty11) · [Retrieval versus answer quality](#term-v17) · [Retry](#term-o07) · [RLHF](#term-t14) · [role hierarchy](#term-g09) · [rollback](#term-o17) · [Routing](#term-agen17)

**S:** [Sandbox](#term-agen16) · [SDK](#term-agen18) · [selective prediction](#term-x09) · [selective risk](#term-v15) · [Self-supervised learning](#term-t03) · [Semantic validation](#term-x07) · [Sensitive information disclosure](#term-sfty04) · [server](#term-agen12) · [SFT](#term-t10) · [Shadow](#term-o16) · [Skill](#term-agen10) · [SLI](#term-o15) · [SLO](#term-o15) · [source support](#term-x04) · [span](#term-o12) · [stale write](#term-o11) · [staleness](#term-rag16) · [state](#term-agen08) · [Statistical uncertainty](#term-v13) · [stop sequence](#term-g07) · [stratification](#term-d12) · [Structured output](#term-g12) · [summarization](#term-g14) · [Supervised learning](#term-t01) · [Supply chain](#term-sfty12) · [Synthetic data](#term-d13) · [Synthetic negative/positive control](#term-v21) · [System instructions](#term-g09) · [System prompt leakage](#term-sfty07)

**T:** [temperature](#term-g05) · [test split](#term-d05) · [throughput](#term-o03) · [Timeout](#term-o06) · [TN](#term-v04) · [Token](#term-g01) · [token probabilities](#term-g04) · [tokenizer](#term-g01) · [Tool](#term-agen04) · [top-k](#term-g06) · [Top-p](#term-g06) · [TP](#term-v04) · [Trace](#term-o12) · [Train](#term-d05) · [Training versus inference](#term-f10) · [Training-serving skew](#term-d11) · [Transformer](#term-f07) · [Transport](#term-agen14) · [Truncation](#term-g15) · [Trust boundary](#term-sfty02) · [TTFT](#term-o03)

**U:** [Unbounded consumption](#term-sfty10) · [underfitting](#term-t18) · [Unit/integration tests versus model evals](#term-v02) · [unknown charge](#term-v20) · [Unsupervised learning](#term-t02) · [unsupported output](#term-x06)

**V:** [validation](#term-d05) · [Vector index](#term-rag07) · [Vector/embedding weakness](#term-sfty09) · [Vercel AI SDK](#term-agen21)

**W:** [weights](#term-f08) · [Workflow](#term-agen01)

**Z:** [Zero-shot](#term-g10)

## Foundations and roles

[Back to top](#glossary-top) · [Term index](#term-index) · [Project evidence](#project-evidence) · [Sources](#primary-sources)

Sources: [S01](#source-s01), [S02](#source-s02), [S04](#source-s04). Project identifiers resolve in [project evidence](#project-evidence).

| ID / term | Meaning | Project example and interview distinction | Related / reading |
| --- | --- | --- | --- |
| <a id="term-f01"></a>[F01](#term-f01) — AI engineering | Building useful systems around AI capabilities, including interfaces, evaluation and operational controls. | [R3](#evidence-r3) observed: model calls are only one component of extraction. Explain the complete outcome and failure policy. | Related: [ML engineering](#term-f02) · [Harness](#term-agen03); Read: [S01](#source-s01), [S02](#source-s02) |
| <a id="term-f02"></a>[F02](#term-f02) — ML engineering | Engineering the data, training, deployment and monitoring lifecycle of learned models. | Conceptual: training/serving a classifier would extend the current inference-focused work. Do not claim training experience from API integration. | Read: [S01](#source-s01), [S02](#source-s02) |
| <a id="term-f03"></a>[F03](#term-f03) — Machine learning / deep learning | ML learns patterns from data; deep learning uses multi-layer neural networks. | Conceptual: a schema validator is deterministic software, not a learned model. | Read: [S01](#source-s01), [S02](#source-s02) |
| <a id="term-f04"></a>[F04](#term-f04) — Generative AI | Models that produce content such as text, images or audio. | [R1](#evidence-r1) observed: producing a PO object is generation even though its output is structured. | Read: [S01](#source-s01), [S02](#source-s02) |
| <a id="term-f05"></a>[F05](#term-f05) — Foundation model / pretrained model | A broadly trained model subsequently adapted or applied to tasks. | [R4](#evidence-r4) observed: existing models are applied to extraction. Pretraining did not happen in rd_ai. | Read: [S01](#source-s01), [S02](#source-s02) |
| <a id="term-f06"></a>[F06](#term-f06) — LLM | Large language model: a model for language/token sequences, often used for generation and reasoning-like tasks. | [R4](#evidence-r4) observed: next-token generation can produce coherent but incorrect ordered rows. Fluency is not truth. | Read: [S01](#source-s01), [S02](#source-s02) |
| <a id="term-f07"></a>[F07](#term-f07) — Transformer / attention | A neural architecture using attention to combine information from sequence positions. | Conceptual: explain contextual token representations; attention is not an application authorization mechanism or a faithful explanation by itself. | Related: [Authentication versus authorization](#term-sfty01); Read: [S01](#source-s01), [S02](#source-s02) |
| <a id="term-f08"></a>[F08](#term-f08) — Parameters / weights | Learned numerical values defining model behavior. | [R4](#evidence-r4) observed comparison; conceptual internals: nominal parameter count does not establish equal task capability. | Read: [S01](#source-s01), [S02](#source-s02) |
| <a id="term-f09"></a>[F09](#term-f09) — Dense model / mixture of experts (MoE) | A dense model uses its parameter blocks throughout; an MoE routes computation through selected experts. | Conceptual: distinguish total parameters from active parameters. Do not invent unpublished provider sizes or infer them from a product name. | Related: [Parameters / weights](#term-f08); Read: [S01](#source-s01), [S02](#source-s02) |
| <a id="term-f10"></a>[F10](#term-f10) — Training versus inference | Training updates learned parameters; inference computes outputs using a model. | [R4](#evidence-r4) observed inference. Running thirty documents does not train Gemma on them automatically. | Related: [Pretraining](#term-t09) · [In-context learning](#term-t17); Read: [S01](#source-s01), [S02](#source-s02) |
| <a id="term-f11"></a>[F11](#term-f11) — Classification / regression | Predicting discrete categories / numerical quantities. | Hypothetical: route document types versus estimate processing time. Extracting a number as text is not automatically a regression model. | Related: [Paired comparison / regression](#term-v10); Read: [S01](#source-s01), [S02](#source-s02) |
| <a id="term-f12"></a>[F12](#term-f12) — Multimodal model | A model accepting or producing multiple modalities, such as text and images. | [A2](#evidence-a2) planned vision; [R4](#evidence-r4) text evidence alone does not demonstrate image understanding. | Read: [S01](#source-s01), [S02](#source-s02) |

## Training and adaptation

[Back to top](#glossary-top) · [Term index](#term-index) · [Project evidence](#project-evidence) · [Sources](#primary-sources)

Sources: [S01](#source-s01), [S04](#source-s04), [S05](#source-s05), [S06](#source-s06). These entries are conceptual unless stated otherwise.

| ID / term | Meaning | Project example and interview distinction | Related / reading |
| --- | --- | --- | --- |
| <a id="term-t01"></a>[T01](#term-t01) — Supervised learning | Learning from inputs paired with target labels. | Hypothetical: train document classification from reviewed examples. Existing approved gold used only for evaluation is not a training run. | Related: [Label / ground truth / gold](#term-d03); Read: [S01](#source-s01), [S04](#source-s04) |
| <a id="term-t02"></a>[T02](#term-t02) — Unsupervised learning | Learning structure without target labels for each example. | Hypothetical: cluster layouts for exploration; clusters are not human-approved business categories. | Read: [S01](#source-s01), [S04](#source-s04) |
| <a id="term-t03"></a>[T03](#term-t03) — Self-supervised learning | Constructing prediction targets from the data itself. | Conceptual: predicting withheld/next tokens differs from manually labeling PO fields. | Read: [S01](#source-s01), [S04](#source-s04) |
| <a id="term-t04"></a>[T04](#term-t04) — Loss function | A numerical objective optimized during training. | Conceptual: training cross-entropy and rd_ai's field-match metric serve different purposes. | Read: [S01](#source-s01), [S04](#source-s04) |
| <a id="term-t05"></a>[T05](#term-t05) — Gradient / backpropagation | Derivatives indicating parameter effects on loss; efficient propagation computes them through a network. | Conceptual: backpropagation is not involved when the coordinator retries an API request. | Read: [S01](#source-s01), [S04](#source-s04) |
| <a id="term-t06"></a>[T06](#term-t06) — Optimizer / learning rate | An update rule and its step-size control. | Conceptual: learning rate changes training updates; temperature changes generation sampling. | Related: [Decoding / temperature](#term-g05); Read: [S01](#source-s01), [S04](#source-s04) |
| <a id="term-t07"></a>[T07](#term-t07) — Batch / epoch | A group processed together / a pass through the training data. | [R4](#evidence-r4) observed document batch is an inference workload, not a training epoch. | Read: [S01](#source-s01), [S04](#source-s04) |
| <a id="term-t08"></a>[T08](#term-t08) — Hyperparameter | A configuration chosen outside the learned weights. | [R4](#evidence-r4) observed temperature and output allowance are inference settings; training settings include learning rate. State which lifecycle you mean. | Related: [Prompt budget / output allowance](#term-g03) · [Decoding / temperature](#term-g05); Read: [S01](#source-s01), [S04](#source-s04) |
| <a id="term-t09"></a>[T09](#term-t09) — Pretraining | Broad initial training before task-specific adaptation. | Conceptual: pretrained model use avoids building this expensive lifecycle inside either project. | Read: [S01](#source-s01), [S04](#source-s04) |
| <a id="term-t10"></a>[T10](#term-t10) — Fine-tuning / SFT | Further weight training; supervised fine-tuning uses input/desired-output examples. | Planned only if separately selected: reviewed data and independent evaluation are needed. A prompt revision is not SFT. | Related: [PEFT / LoRA](#term-t11) · [RAG versus fine-tuning](#term-rag17); Read: [S01](#source-s01), [S04](#source-s04) |
| <a id="term-t11"></a>[T11](#term-t11) — PEFT / LoRA | Parameter-efficient fine-tuning updates a small subset; low-rank adaptation trains compact update matrices. | Hypothetical local adaptation study. LoRA reduces trainable updates, not the need for trustworthy data and validation. | Related: [Fine-tuning / SFT](#term-t10); Read: [S05](#source-s05) |
| <a id="term-t12"></a>[T12](#term-t12) — Distillation | Training a student using signals from a teacher system. | Hypothetical: provider-generated candidates need review and exposure tracking; saving provider predictions alone is not distillation. | Read: [S01](#source-s01), [S04](#source-s04) |
| <a id="term-t13"></a>[T13](#term-t13) — Reinforcement learning | Learning decisions from rewards through interaction. | Conceptual: bounded retry logic and user approval are not RL training. | Read: [S01](#source-s01), [S04](#source-s04) |
| <a id="term-t14"></a>[T14](#term-t14) — RLHF / DPO | Reinforcement learning from human feedback / direct preference optimization: different approaches to preference-based post-training. | Conceptual: a review UI does not perform either method unless a selected training process actually consumes feedback. | Read: [S01](#source-s01), [S04](#source-s04) |
| <a id="term-t15"></a>[T15](#term-t15) — Alignment | Efforts to make behavior match intended objectives and constraints. | [R3](#evidence-r3)/[A2](#evidence-a2): model behavior and independently enforced authority both matter. Alignment is not a guarantee of safe application actions. | Read: [S01](#source-s01), [S04](#source-s04) |
| <a id="term-t16"></a>[T16](#term-t16) — Quantization | Lower-precision representation of weights and/or activations for resource trade-offs. | [R4](#evidence-r4) observed quantized local model; savings and quality changes require measurement, not a fixed universal speed claim. | Related: [Precision / recall / F1](#term-v05) · [Parameters / weights](#term-f08); Read: [S06](#source-s06) |
| <a id="term-t17"></a>[T17](#term-t17) — In-context learning | Behavior guided by instructions/examples in the current context without a weight update. | [R5](#evidence-r5) observed example resources. Removing examples from the request can remove their influence; it is not persistent training. | Related: [Zero-shot / few-shot](#term-g10) · [Skill / instruction resource](#term-agen10); Read: [S01](#source-s01), [S04](#source-s04) |
| <a id="term-t18"></a>[T18](#term-t18) — Overfitting / underfitting | Excessive adaptation to seen patterns / insufficient capture of useful patterns. | [R2](#evidence-r2) observed exposure risk: repeated gold-guided prompt tuning can overfit development cases without training weights. Do not diagnose all errors as insufficient model size. | Related: [Parameters / weights](#term-f08) · [Label / ground truth / gold](#term-d03); Read: [S08](#source-s08) |

## Data and generalization

[Back to top](#glossary-top) · [Term index](#term-index) · [Project evidence](#project-evidence) · [Sources](#primary-sources)

Sources: [S01](#source-s01), [S07](#source-s07), [S08](#source-s08); project-specific authority comes from [R1](#evidence-r1)/[R2](#evidence-r2).

| ID / term | Meaning | Project example and interview distinction | Related / reading |
| --- | --- | --- | --- |
| <a id="term-d01"></a>[D01](#term-d01) — Dataset / corpus | A defined collection of examples; a corpus commonly contains text/documents. | [R1](#evidence-r1) observed: thirty approved neutral inputs; membership and hashes define the population. | Read: [S07](#source-s07), [S08](#source-s08) |
| <a id="term-d02"></a>[D02](#term-d02) — Feature / representation | Information presented to a learned system and its encoding. | [R5](#evidence-r5) observed source representations. A JSON output field is not necessarily an input feature or a feature-store entry. | Read: [S07](#source-s07), [S08](#source-s08) |
| <a id="term-d03"></a>[D03](#term-d03) — Label / ground truth / gold | A reference target accepted under an explicit labeling authority. | [R1](#evidence-r1) observed: ten approved gold POs; twenty inputs remain unlabeled. A plausible provider answer is not automatically gold. | Related: [Annotation versus approval](#term-d04) · [Leakage / contamination](#term-d07); Read: [S07](#source-s07), [S08](#source-s08) |
| <a id="term-d04"></a>[D04](#term-d04) — Annotation versus approval | Annotation records interpretation; approval grants the stated reference authority. | [R1](#evidence-r1) observed: agent explanations do not constitute another human labeling pass. | Related: [Agent](#term-agen02); Read: [S07](#source-s07), [S08](#source-s08) |
| <a id="term-d05"></a>[D05](#term-d05) — Train / validation / test split | Data for learning, selection/tuning and final assessment, respectively. | [R2](#evidence-r2) observed development gold is reused; renaming it test data does not make it independent. | Related: [Label / ground truth / gold](#term-d03); Read: [S07](#source-s07), [S08](#source-s08) |
| <a id="term-d06"></a>[D06](#term-d06) — Holdout / grouped split | Reserved evaluation data; groups prevent related sources/layouts crossing partitions. | [R2](#evidence-r2) observed twenty-five connected source/layout groups. Shared-source OR shared-layout relationships are transitive. | Read: [S07](#source-s07), [S08](#source-s08) |
| <a id="term-d07"></a>[D07](#term-d07) — Leakage / contamination | Evaluation information influences training, tuning or context in a way that compromises the intended measurement. | [R2](#evidence-r2): gold/predictions must not enter a retrieval collection used to claim independent extraction accuracy. | Related: [Exposure history](#term-d08) · [Development set / independent evaluation](#term-v12); Read: [S07](#source-s07), [S08](#source-s08) |
| <a id="term-d08"></a>[D08](#term-d08) — Exposure history | Record of how cases were seen or used during development. | [R2](#evidence-r2) observed inventory keeps unknown inspection history unknown. Unlabeled does not mean unseen. | Read: [S07](#source-s07), [S08](#source-s08) |
| <a id="term-d09"></a>[D09](#term-d09) — Generalization / distribution shift | Performance beyond development examples / a change in the data-generating environment. | Hypothetical: a new supplier layout or language. Ten reused gold cases cannot establish broad reliability. | Related: [Label / ground truth / gold](#term-d03); Read: [S07](#source-s07), [S08](#source-s08) |
| <a id="term-d10"></a>[D10](#term-d10) — Data drift / concept drift | Change in input distribution / change in the relationship between input and target. | Hypothetical: scan quality changes versus a changed business definition of an ordered row. The remedies differ. | Read: [S07](#source-s07), [S08](#source-s08) |
| <a id="term-d11"></a>[D11](#term-d11) — Training-serving skew | A mismatch between training-time and serving-time processing/data behavior. | Hypothetical classifier: different date normalization at serving. Runtime/prompt drift in an API application is related but not automatically training-serving skew. | Read: [S07](#source-s07), [S08](#source-s08) |
| <a id="term-d12"></a>[D12](#term-d12) — Class imbalance / stratification | Unequal class prevalence / preserving relevant strata in sampling. | [R2](#evidence-r2): many expected-null fields can mask weak present-value extraction; report the populations separately. | Read: [S07](#source-s07), [S08](#source-s08) |
| <a id="term-d13"></a>[D13](#term-d13) — Synthetic data / augmentation | Invented examples / transformed examples for a declared purpose. | [R2](#evidence-r2) observed technical controls; they are not new approved customer gold or proof of real-world coverage. | Related: [Label / ground truth / gold](#term-d03); Read: [S07](#source-s07), [S08](#source-s08) |
| <a id="term-d14"></a>[D14](#term-d14) — Data lineage / provenance | Traceable origin, transformations, versions and dependencies. | [R1](#evidence-r1)/[R6](#evidence-r6) observed hashes and manifests; [A1](#evidence-a1) documented artifact ownership. A hash identifies bytes, not factual correctness. | Read: [S07](#source-s07), [S08](#source-s08) |
| <a id="term-d15"></a>[D15](#term-d15) — Dataset versioning / reproducibility | Retaining the exact data/configuration needed to repeat a measurement. | [R6](#evidence-r6) observed archive-bound reproduction. Recomputing saved records differs from reproducing stochastic generation. | Read: [S07](#source-s07), [S08](#source-s08) |
| <a id="term-d16"></a>[D16](#term-d16) — Feature store / model registry | Systems for managed feature definitions/serving and model-version lifecycle metadata. | Conceptual: Garage holds artifacts, not automatically a feature store or model registry. Adopt infrastructure only for a real lifecycle need. | Read: [S07](#source-s07), [S08](#source-s08) |

## Tokens, prompting and generation

[Back to top](#glossary-top) · [Term index](#term-index) · [Project evidence](#project-evidence) · [Sources](#primary-sources)

Sources: [S03](#source-s03), [S09](#source-s09), [S10](#source-s10). For saved experiments see [R4](#evidence-r4)/[R5](#evidence-r5).

| ID / term | Meaning | Project example and interview distinction | Related / reading |
| --- | --- | --- | --- |
| <a id="term-g01"></a>[G01](#term-g01) — Token / tokenizer | A model-specific sequence unit / conversion between content and token IDs. | [R4](#evidence-r4) observed tokenizer-bound admission. Character or byte length is not an exact token count. | Read: [S09](#source-s09), [S10](#source-s10) |
| <a id="term-g02"></a>[G02](#term-g02) — Context window | The runtime/model's bounded working sequence capacity. | [R4](#evidence-r4) observed native context experiments. Larger capacity does not ensure correct ordered-row selection. | Related: [Prompt budget / output allowance](#term-g03) · [Truncation / finish reason](#term-g15); Read: [S09](#source-s09), [S10](#source-s10) |
| <a id="term-g03"></a>[G03](#term-g03) — Prompt budget / output allowance | Capacity allocated to request context / permitted generated completion. | [R4](#evidence-r4) observed 4,096/8,192/16,384 output diagnostics. Increasing output allowance can enable more erroneous output as well as avoid truncation. | Related: [Context window](#term-g02) · [Chain of thought / reasoning model](#term-g11); Read: [S09](#source-s09), [S10](#source-s10) |
| <a id="term-g04"></a>[G04](#term-g04) — Logits / token probabilities | Raw scores / normalized next-token likelihoods. | Conceptual: token likelihood is not calibrated confidence that a PO field is supported by its source. | Read: [S09](#source-s09), [S10](#source-s10) |
| <a id="term-g05"></a>[G05](#term-g05) — Decoding / temperature | Output selection procedure / a parameter changing the probability distribution's concentration. | [R4](#evidence-r4) observed sampling profiles. Temperature zero does not guarantee identical outputs across runtime updates or hardware. | Related: [Top-p / top-k](#term-g06) · [Optimizer / learning rate](#term-t06); Read: [S09](#source-s09), [S10](#source-s10) |
| <a id="term-g06"></a>[G06](#term-g06) — Top-p / top-k | Sampling from a cumulative-probability candidate set / a fixed-size candidate set. | [R4](#evidence-r4) observed top-p; top-k is conditional on runtime support. Retrieval top-k is a different operation. | Related: [RAG](#term-rag01); Read: [S09](#source-s09), [S10](#source-s10) |
| <a id="term-g07"></a>[G07](#term-g07) — Repetition penalty / stop sequence | A generation bias against repeats / a termination trigger. | Hypothetical diagnostic: real repeated product rows must not be deleted merely because text repeats. | Read: [S09](#source-s09), [S10](#source-s10) |
| <a id="term-g08"></a>[G08](#term-g08) — Prompt engineering | Designing request instructions, examples and formatting. | [R5](#evidence-r5) observed frozen v1/v2 and example trials. Compare changed factors explicitly. | Read: [S09](#source-s09), [S10](#source-s10) |
| <a id="term-g09"></a>[G09](#term-g09) — System instructions / role hierarchy | Trusted instruction channels and their precedence within a provider interface. | [R3](#evidence-r3): application authorization still operates outside the model. Text saying "system" inside a document does not grant authority. | Related: [Authentication versus authorization](#term-sfty01); Read: [S09](#source-s09), [S10](#source-s10) |
| <a id="term-g10"></a>[G10](#term-g10) — Zero-shot / few-shot | Task instruction without examples / with a small set of examples. | [R5](#evidence-r5) observed both approaches. Examples used for tuning must be disclosed in evaluation. | Read: [S09](#source-s09), [S10](#source-s10) |
| <a id="term-g11"></a>[G11](#term-g11) — Chain of thought / reasoning model | Intermediate reasoning behavior / a model trained to perform more extensive internal reasoning. | [R4](#evidence-r4) observed thinking controls and output truncation. Assess answers and actions; do not require private reasoning disclosure. | Read: [S09](#source-s09), [S10](#source-s10) |
| <a id="term-g12"></a>[G12](#term-g12) — Structured output / constrained decoding | Output shaped by a contract; decoding may restrict allowed token sequences. | [R1](#evidence-r1) observed JSON/schema validation. Valid JSON, schema validity and factual correctness are distinct. | Related: [Semantic validation](#term-x07) · [Improper output handling](#term-sfty06); Read: [S09](#source-s09), [S10](#source-s10) |
| <a id="term-g13"></a>[G13](#term-g13) — Context engineering | Selecting and managing instructions, evidence, tools and state available to a model. | [R5](#evidence-r5) observed source views; [A2](#evidence-a2) planned field-scoped context. Prompt wording is only part of this responsibility. | Read: [S03](#source-s03) |
| <a id="term-g14"></a>[G14](#term-g14) — Context compaction / summarization | Reducing retained context, often by summaries or selective retention. | Planned P04: test lost constraints and unresolved questions. Compaction can discard evidence. | Read: [S03](#source-s03) |
| <a id="term-g15"></a>[G15](#term-g15) — Truncation / finish reason | Incomplete output due to a limit or interruption / reported termination metadata. | [R3](#evidence-r3)/[R4](#evidence-r4) observed: retain failures and raw response evidence; do not rescue partial JSON into a factual success. | Read: [S09](#source-s09), [S10](#source-s10) |
| <a id="term-g16"></a>[G16](#term-g16) — Prompt injection | Untrusted input attempts to redirect model behavior or policy. | [R2](#evidence-r2) technical controls; real model attack susceptibility remains unmeasured. See security entries for authority boundaries. | Read: [S22](#source-s22) |
| <a id="term-g17"></a>[G17](#term-g17) — Prompt caching / response caching | Reusing compatible prefix computation / reusing an earlier application answer. | Planned P05: different cache keys, validity and billing semantics. Neither means the model learned a document. | Related: [KV cache](#term-o02) · [Index lifecycle / staleness](#term-rag16); Read: [S09](#source-s09), [S10](#source-s10) |
| <a id="term-g18"></a>[G18](#term-g18) — Prompt/model/schema version | An identity for a behavior-affecting artifact. | [R2](#evidence-r2)/[R6](#evidence-r6) observed bindings. A mutable model tag alone is insufficient to identify a measured local runtime. | Read: [S09](#source-s09), [S10](#source-s10) |

## Documents, grounding and decisions

[Back to top](#glossary-top) · [Term index](#term-index) · [Project evidence](#project-evidence) · [Sources](#primary-sources)

Sources: [R1](#evidence-r1), [R2](#evidence-r2), [R5](#evidence-r5) and the generic [E1](#evidence-e1)–[E3](#evidence-e3) reference patterns.

| ID / term | Meaning | Project example and interview distinction | Related / reading |
| --- | --- | --- | --- |
| <a id="term-x01"></a>[X01](#term-x01) — OCR versus text extraction | Recognizing text from images versus reading existing document text content. | [A2](#evidence-a2) planned vision; [E1](#evidence-e1) documented extraction preparation. Reading a digital PDF does not establish OCR capability. | Read: [S13](#source-s13) |
| <a id="term-x02"></a>[X02](#term-x02) — Layout/table understanding | Interpreting rows, columns, headers, blanks and relationships. | [R5](#evidence-r5) observed catalog/order ambiguity. Token availability alone does not preserve table semantics. | Read: [S13](#source-s13) |
| <a id="term-x03"></a>[X03](#term-x03) — Extraction versus normalization | Selecting source values versus converting representations under explicit rules. | [R1](#evidence-r1) observed exact-value scoring; silent decimal/date repair changes the measurement contract. | Read: [S13](#source-s13) |
| <a id="term-x04"></a>[X04](#term-x04) — Grounding / source support | Connecting a claim to evidence that actually supports it. | Planned P02 provenance; observed [R5](#evidence-r5) diagnostics remain limited. A matching string can have the wrong business role. | Related: [Citation / provenance span](#term-x05) · [Faithfulness / citation correctness](#term-rag15); Read: [S13](#source-s13) |
| <a id="term-x05"></a>[X05](#term-x05) — Citation / provenance span | A reference to evidence / precise source location. | Planned P02/P03. Coordinates lost during text projection must not be invented later. | Read: [S13](#source-s13) |
| <a id="term-x06"></a>[X06](#term-x06) — Hallucination / unsupported output | Generated content lacking a reliable basis in the relevant evidence. | [R5](#evidence-r5) observed unsupported catalog rows. Distinguish invented content, wrong-role copying and representation mismatch. | Read: [S13](#source-s13) |
| <a id="term-x07"></a>[X07](#term-x07) — Semantic validation | Checking business meaning beyond structural constraints. | [R1](#evidence-r1) rejects invalid shapes; source-role validation is a separate responsibility. Schema validity cannot certify an order was placed. | Related: [Structured output / constrained decoding](#term-g12); Read: [S13](#source-s13) |
| <a id="term-x08"></a>[X08](#term-x08) — Confidence / calibration | Estimated certainty / agreement between stated confidence and observed correctness. | Hypothetical reviewed study: "90% confident" needs an outcome population and reliability analysis. | Related: [Judge calibration / false acceptance](#term-v14) · [Coverage / selective risk](#term-v15); Read: [S13](#source-s13) |
| <a id="term-x09"></a>[X09](#term-x09) — Abstention / selective prediction | Explicitly declining to decide when evidence or reliability is insufficient. | [R2](#evidence-r2) observed rubric: refusal, all-null objects and parsing failure do not automatically count as successful abstention. | Related: [Coverage / selective risk](#term-v15) · [Proposal versus application](#term-x11); Read: [S13](#source-s13) |
| <a id="term-x10"></a>[X10](#term-x10) — Human in the loop | A defined human review/decision step within a system. | [A2](#evidence-a2) planned; [E3](#evidence-e3) documented reference. The human needs source evidence and a meaningful reject/no-change option. | Read: [S13](#source-s13) |
| <a id="term-x11"></a>[X11](#term-x11) — Proposal versus application | A candidate change versus an authorized durable mutation. | [A2](#evidence-a2) planned independent approval; [E3](#evidence-e3) documented read/write separation. A model explanation is not permission to submit. | Read: [S13](#source-s13) |
| <a id="term-x12"></a>[X12](#term-x12) — Immutable baseline / correction overlay | Preserved extraction plus separate edits applied under rules. | [A1](#evidence-a1) documented architecture; [E3](#evidence-e3) documented reference. Corrections should not silently erase the evidence being evaluated. | Read: [S13](#source-s13) |

## Evaluation and statistics

[Back to top](#glossary-top) · [Term index](#term-index) · [Project evidence](#project-evidence) · [Sources](#primary-sources)

Sources: [S11](#source-s11), [S12](#source-s12), [S13](#source-s13); exact local scoring is defined by [R1](#evidence-r1)/[R2](#evidence-r2).

| ID / term | Meaning | Project example and interview distinction | Related / reading |
| --- | --- | --- | --- |
| <a id="term-v01"></a>[V01](#term-v01) — Evaluation / benchmark / baseline | Measuring defined behavior / a comparison task set / an initial reference system. | [R2](#evidence-r2) observed protocol. A test suite, public leaderboard and application acceptance set answer different questions. | Read: [S11](#source-s11), [S12](#source-s12) |
| <a id="term-v02"></a>[V02](#term-v02) — Unit/integration tests versus model evals | Code-behavior checks versus measurements of model/system task performance. | [R2](#evidence-r2) observed 982-test gate is historical implementation evidence, not 982 independent model-accuracy cases. | Read: [S11](#source-s11), [S12](#source-s12) |
| <a id="term-v03"></a>[V03](#term-v03) — Deterministic, human and model-based evals | Rule-based scoring, reviewed judgment and model judgment. | [R2](#evidence-r2) observed deterministic capability; new human semantic anchors and judge calibration remain unselected. | Related: [Confidence / calibration](#term-x08); Read: [S11](#source-s11), [S12](#source-s12) |
| <a id="term-v04"></a>[V04](#term-v04) — TP / FP / FN / TN | Correct positive, incorrect positive, missed positive and correct negative for a defined decision. | Hypothetical support classifier: specify whether positive means "supported" or "needs review" before counting errors. | Read: [S11](#source-s11), [S12](#source-s12) |
| <a id="term-v05"></a>[V05](#term-v05) — Precision / recall / F1 | TP/(TP+FP), TP/(TP+FN), and their harmonic mean. | Hypothetical detector study: name the unit and undefined-denominator handling. Do not relabel field-match accuracy as precision. | Read: [S11](#source-s11), [S12](#source-s12) |
| <a id="term-v06"></a>[V06](#term-v06) — Accuracy / exact match | Fraction correct under a defined unit / complete equality under the contract. | [R1](#evidence-r1) observed field accuracy differs from exact-document rate. State denominator and matching rules. | Related: [Micro / macro aggregation](#term-v07) · [Positional matching / alignment](#term-v09); Read: [S13](#source-s13) |
| <a id="term-v07"></a>[V07](#term-v07) — Micro / macro aggregation | Pooling counts before division / averaging per-group or per-example scores. | [R1](#evidence-r1) observed micro field scoring. Macro results need an explicit averaging unit and missing-value policy. | Read: [S13](#source-s13) |
| <a id="term-v08"></a>[V08](#term-v08) — Present/null populations | Separate metrics for reference values that exist versus are absent. | [R2](#evidence-r2) observed: high null agreement can coexist with weak extraction of actual values. | Read: [S13](#source-s13) |
| <a id="term-v09"></a>[V09](#term-v09) — Positional matching / alignment | Comparing rows by contract order versus establishing another correspondence. | [R1](#evidence-r1) observed positional scoring; missing/extra rows affect denominators. Semantic rematching would be a separate metric. | Read: [S13](#source-s13) |
| <a id="term-v10"></a>[V10](#term-v10) — Paired comparison / regression | Before/after outcomes on the same units / deterioration in some behavior. | [R2](#evidence-r2) observed 46 gold-field improvements and 12 regressions. An aggregate gain does not mean every case improved. | Related: [Ablation / controlled experiment](#term-v11) · [Development set / independent evaluation](#term-v12); Read: [S13](#source-s13) |
| <a id="term-v11"></a>[V11](#term-v11) — Ablation / controlled experiment | Removing a component / varying specified factors while checking comparability. | [R4](#evidence-r4)/[R5](#evidence-r5) observed interventions. A combined prompt/model/context change cannot isolate each contribution. | Read: [S11](#source-s11), [S12](#source-s12) |
| <a id="term-v12"></a>[V12](#term-v12) — Development set / independent evaluation | Cases informing choices / assessment not compromised by those choices. | [R2](#evidence-r2) observed reused gold10. A successful score on it is not unseen-layout validation. | Read: [S11](#source-s11), [S12](#source-s12) |
| <a id="term-v13"></a>[V13](#term-v13) — Statistical uncertainty / confidence interval | Quantified uncertainty under an explicit sampling model. | [R2](#evidence-r2): related layouts and ten reused cases limit inference; do not treat every field as an independent sample. | Read: [S11](#source-s11), [S12](#source-s12) |
| <a id="term-v14"></a>[V14](#term-v14) — Judge calibration / false acceptance | Checking judge agreement against reviewed anchors / accepting an anchored wrong outcome. | Planned C01 only. A judge's own answer cannot serve as its calibration truth. | Related: [Deterministic, human and model-based evals](#term-v03) · [Confidence / calibration](#term-x08); Read: [S12](#source-s12) |
| <a id="term-v15"></a>[V15](#term-v15) — Coverage / selective risk | Fraction of cases receiving a decision / error rate among decided cases. | Hypothetical abstention study: report both; perfect accuracy after declining almost everything may be unusable. | Related: [Abstention / selective prediction](#term-x09); Read: [S11](#source-s11), [S12](#source-s12) |
| <a id="term-v16"></a>[V16](#term-v16) — Perplexity | Exponentiated average token prediction loss under a specified tokenization/setup. | Conceptual: it is not a direct score of factual PO extraction or safe tool use. | Read: [S11](#source-s11), [S12](#source-s12) |
| <a id="term-v17"></a>[V17](#term-v17) — Retrieval versus answer quality | Whether useful evidence was found versus whether the final response used it correctly. | Planned P03. A correct answer can arise from irrelevant retrieval, and good retrieval can still yield a bad answer. | Related: [RAG](#term-rag01); Read: [S11](#source-s11), [S12](#source-s12) |
| <a id="term-v18"></a>[V18](#term-v18) — Offline eval / online experiment | Measurement on saved/controlled cases versus a deployed user/workload experiment. | [R2](#evidence-r2) observed offline reproduction. It is not a live A/B test or production quality guarantee. | Read: [S11](#source-s11), [S12](#source-s12) |
| <a id="term-v19"></a>[V19](#term-v19) — Latency percentile / population | A ranked duration statistic for a stated set of operations. | [R1](#evidence-r1) observed retry-inclusive p50/p95 on attempted inputs. Excluding failures can mislead; p95 of ten samples is fragile. | Read: [S13](#source-s13), [S19](#source-s19) |
| <a id="term-v20"></a>[V20](#term-v20) — Known cost / reservation / unknown charge | Reported actual charge / held allowance / unresolved billing outcome. | [R3](#evidence-r3) observed accounting. A reservation is not a bill and a missing charge is not zero. | Read: [S13](#source-s13) |
| <a id="term-v21"></a>[V21](#term-v21) — Synthetic negative/positive control | A known bad/good condition testing whether a check behaves as intended. | [R2](#evidence-r2) observed changed-result/hash/record rejections and positive reproduction. They prove bounded mechanisms, not general model safety. | Read: [S11](#source-s11), [S12](#source-s12) |

## Retrieval and RAG

[Back to top](#glossary-top) · [Term index](#term-index) · [Project evidence](#project-evidence) · [Sources](#primary-sources)

Sources: [S14](#source-s14), [S15](#source-s15); these are planned P03 examples unless marked otherwise.

| ID / term | Meaning | Project example and interview distinction | Related / reading |
| --- | --- | --- | --- |
| <a id="term-rag01"></a>[RAG01](#term-rag01) — RAG | Retrieval-augmented generation supplies selected external evidence during generation. | Planned P03 field-rule answers. RAG changes request evidence; it does not inherently update model weights. | Related: [Parameters / weights](#term-f08); Read: [S14](#source-s14), [S15](#source-s15) |
| <a id="term-rag02"></a>[RAG02](#term-rag02) — Embedding | A learned numerical representation used for tasks such as similarity. | Planned rule retrieval. Similarity is not proof that a rule authorizes an action. | Related: [RAG](#term-rag01); Read: [S14](#source-s14), [S15](#source-s15) |
| <a id="term-rag03"></a>[RAG03](#term-rag03) — Dense versus sparse retrieval | Search using learned dense vectors versus sparse lexical representations. | Planned keyword/embedding comparison. Exact product codes can favor lexical methods. | Read: [S14](#source-s14), [S15](#source-s15) |
| <a id="term-rag04"></a>[RAG04](#term-rag04) — BM25 | A lexical ranking function based on term occurrence and document statistics. | Hypothetical keyword baseline before embeddings. It does not require an LLM. | Related: [Embedding](#term-rag02); Read: [S14](#source-s14), [S15](#source-s15) |
| <a id="term-rag05"></a>[RAG05](#term-rag05) — Cosine / dot product / distance | Different comparisons between representations. | Hypothetical index configuration: normalization and model training affect which metric is appropriate. | Read: [S14](#source-s14), [S15](#source-s15) |
| <a id="term-rag06"></a>[RAG06](#term-rag06) — Chunking / overlap | Dividing sources into retrieval units / retaining shared boundary content. | Planned P03: preserve rule headers and source IDs. More overlap can increase duplication and cost. | Related: [RAG](#term-rag01); Read: [S14](#source-s14), [S15](#source-s15) |
| <a id="term-rag07"></a>[RAG07](#term-rag07) — Vector index / database | A search structure for vectors / storage and operational capabilities around them. | Planned one selected store. FAISS, managed databases and relational extensions are not identical products. | Read: [S14](#source-s14), [S15](#source-s15) |
| <a id="term-rag08"></a>[RAG08](#term-rag08) — ANN / HNSW | Approximate nearest-neighbor search / a graph-based ANN method. | Conceptual store experiment: speed, memory and retrieval recall trade off. Exact search can be a small-corpus baseline. | Related: [RAG](#term-rag01) · [Memory / state / history](#term-agen08); Read: [S14](#source-s14), [S15](#source-s15) |
| <a id="term-rag09"></a>[RAG09](#term-rag09) — Hybrid search | Combining lexical and dense retrieval results. | Conditional P03 extension. It needs evaluation and a ranking/fusion policy, not just two indexes. | Related: [RAG](#term-rag01); Read: [S14](#source-s14), [S15](#source-s15) |
| <a id="term-rag10"></a>[RAG10](#term-rag10) — Bi-encoder / cross-encoder reranking | Independent query/document representations / joint scoring of candidate pairs. | Conditional retrieve-then-rerank trial. Reranking adds work and cannot recover relevant sources never retrieved. | Read: [S14](#source-s14), [S15](#source-s15) |
| <a id="term-rag11"></a>[RAG11](#term-rag11) — Query rewriting | Transforming a query to improve evidence retrieval. | Hypothetical field-name expansion. Preserve user intent, scope and the original query for analysis. | Related: [RAG](#term-rag01); Read: [S14](#source-s14), [S15](#source-s15) |
| <a id="term-rag12"></a>[RAG12](#term-rag12) — Metadata filtering / authorized retrieval | Restricting candidates by properties and trusted access policy. | Planned P03 fictional principals and rule versions. Filtering only after context construction can already leak evidence. | Read: [S14](#source-s14), [S15](#source-s15) |
| <a id="term-rag13"></a>[RAG13](#term-rag13) — Recall@k / precision@k | Relevant evidence recovered / relevance among the returned top-k items. | Planned reviewed relevance cases. This k is a retrieval cutoff, not generation top-k sampling. | Related: [RAG](#term-rag01); Read: [S14](#source-s14), [S15](#source-s15) |
| <a id="term-rag14"></a>[RAG14](#term-rag14) — MRR / nDCG | Mean reciprocal first-relevant rank / a position-discounted graded-relevance score. | Conceptual ranking study: both require clear relevance labels; neither measures final answer truth. | Read: [S14](#source-s14), [S15](#source-s15) |
| <a id="term-rag15"></a>[RAG15](#term-rag15) — Faithfulness / citation correctness | Whether claims follow supplied evidence / cited sources support the specific claims. | Planned P03. A citation's existence does not establish entailment or completeness. | Read: [S14](#source-s14), [S15](#source-s15) |
| <a id="term-rag16"></a>[RAG16](#term-rag16) — Index lifecycle / staleness | Building, updating, deleting and versioning searchable evidence. | Planned P03/P05: deleted or superseded rules must not survive through stale indexes/caches. | Read: [S14](#source-s14), [S15](#source-s15) |
| <a id="term-rag17"></a>[RAG17](#term-rag17) — RAG versus fine-tuning | Providing external knowledge at inference versus adapting parameters. | Future choice: current business rules often need explicit retrieval; recurring behavior adaptation might justify training. Neither approach automatically solves correctness. | Related: [RAG](#term-rag01) · [Fine-tuning / SFT](#term-t10); Read: [S14](#source-s14), [S15](#source-s15) |

## Agents, tools and context

[Back to top](#glossary-top) · [Term index](#term-index) · [Project evidence](#project-evidence) · [Sources](#primary-sources)

Sources: [S03](#source-s03), [S16](#source-s16), [S17](#source-s17), [S18](#source-s18). A graph or an agent framework alone is not evidence of model-directed agency.

| ID / term | Meaning | Project example and interview distinction | Related / reading |
| --- | --- | --- | --- |
| <a id="term-agen01"></a>[AGEN01](#term-agen01) — Workflow / pipeline / DAG | Application-defined steps; a directed acyclic graph represents dependencies without cycles. | [R3](#evidence-r3) observed deterministic execution; [E1](#evidence-e1) documented orchestration. Do not call every multi-step flow an autonomous agent. | Related: [Agent](#term-agen02); Read: [S16](#source-s16), [S03](#source-s03) |
| <a id="term-agen02"></a>[AGEN02](#term-agen02) — Agent | A system where a model directs some sequence of actions using observations and tools. | Planned P04/[A2](#evidence-a2). Identify exactly which decisions the model owns and which remain application policy. | Related: [Workflow / pipeline / DAG](#term-agen01) · [Harness](#term-agen03); Read: [S16](#source-s16), [S03](#source-s03) |
| <a id="term-agen03"></a>[AGEN03](#term-agen03) — Harness | Surrounding execution environment providing tools, state, validation, limits and evidence. | [R3](#evidence-r3) observed application harness. A raw local model does not automatically discover repository skills or gain tool access. | Read: [S16](#source-s16), [S03](#source-s03) |
| <a id="term-agen04"></a>[AGEN04](#term-agen04) — Tool / function calling | Structured model requests for application-defined capabilities. | Planned typed read/proposal tools. Model-generated arguments require independent validation and authorization. | Related: [MCP](#term-agen11) · [Excessive agency](#term-sfty05); Read: [S16](#source-s16), [S03](#source-s03) |
| <a id="term-agen05"></a>[AGEN05](#term-agen05) — ReAct | A pattern alternating model deliberation/action selection with tool observations. | Conditional P04. Expose action/result traces; private reasoning text is not required for audit. | Read: [S16](#source-s16), [S03](#source-s03) |
| <a id="term-agen06"></a>[AGEN06](#term-agen06) — Planner/executor / orchestrator-workers | Separating task decomposition from execution or delegation. | Hypothetical bounded assistant. Additional roles must earn their complexity through measured results. | Read: [S16](#source-s16), [S03](#source-s03) |
| <a id="term-agen07"></a>[AGEN07](#term-agen07) — Multi-agent system | Multiple agent roles/processes coordinating on work. | Conditional P04: count every role's tokens/time/failures. Multiple ordinary backend services are not automatically multiple AI agents. | Related: [Agent](#term-agen02); Read: [S16](#source-s16), [S03](#source-s03) |
| <a id="term-agen08"></a>[AGEN08](#term-agen08) — Memory / state / history | Persisted or retained information used across steps or requests. | Planned document-scoped context; [A1](#evidence-a1) observed application state is separate from model memory. Persisted conversation is not a weight update. | Read: [S16](#source-s16), [S03](#source-s03) |
| <a id="term-agen09"></a>[AGEN09](#term-agen09) — Context isolation | Preventing one principal/session/document's information from entering another's context improperly. | Planned P04/P05; [A1](#evidence-a1) authorization foundation. Add identity/version-aware boundaries, not just different prompt labels. | Related: [Authentication versus authorization](#term-sfty01); Read: [S16](#source-s16), [S03](#source-s03) |
| <a id="term-agen10"></a>[AGEN10](#term-agen10) — Skill / instruction resource | Packaged task instructions and optional resources loaded by a supporting harness. | [R5](#evidence-r5) observed resource-loaded examples. A skill extends available guidance; it is not fine-tuning or inherently executable authority. | Related: [In-context learning](#term-t17) · [Harness](#term-agen03); Read: [S16](#source-s16), [S03](#source-s03) |
| <a id="term-agen11"></a>[AGEN11](#term-agen11) — MCP | Model Context Protocol: an integration protocol for exposing capabilities/context to AI applications. | Conditional local slice in P04/AI20. It is neither a model nor an authorization replacement. | Related: [MCP host / client / server](#term-agen12) · [A2A](#term-agen15); Read: [S17](#source-s17) |
| <a id="term-agen12"></a>[AGEN12](#term-agen12) — MCP host / client / server | Host application manages integration; client communicates; server exposes capabilities. | Planned exercise: a real client calls one server wrapping existing domain tools. Domain behavior should remain reusable outside MCP. | Related: [MCP](#term-agen11); Read: [S17](#source-s17) |
| <a id="term-agen13"></a>[AGEN13](#term-agen13) — MCP tools / resources / prompts | Callable operations, addressable contextual data and reusable prompt templates. | Conceptual interface design. Availability does not mean a principal may use every capability. | Read: [S17](#source-s17) |
| <a id="term-agen14"></a>[AGEN14](#term-agen14) — Transport / protocol | How messages travel / their meaning and interaction rules. | Planned local/remote MCP: transport selection and remote authentication are separate decisions. Verify current protocol requirements before implementation. | Related: [MCP](#term-agen11); Read: [S17](#source-s17) |
| <a id="term-agen15"></a>[AGEN15](#term-agen15) — A2A | Agent2Agent protocol for interoperable agent applications. | Conceptual, not selected. Contrast agent-to-agent task exchange with MCP integration to tools/context. | Related: [Agent](#term-agen02) · [MCP](#term-agen11); Read: [S18](#source-s18) |
| <a id="term-agen16"></a>[AGEN16](#term-agen16) — Sandbox / capability boundary | Confinement of accessible resources and effects. | [R3](#evidence-r3) observed bounded execution; planned tools must not gain unrestricted file/network or submission access. A prompt is not a sandbox. | Read: [S16](#source-s16), [S03](#source-s03) |
| <a id="term-agen17"></a>[AGEN17](#term-agen17) — Routing / fallback | Selecting a model/path / taking a defined alternative after a condition. | Conditional stronger-provider routing study. A cheap model needs a trustworthy escalation signal; confidence claims alone are insufficient. | Read: [S16](#source-s16), [S03](#source-s03) |
| <a id="term-agen18"></a>[AGEN18](#term-agen18) — Agent framework / SDK | Libraries for model interaction, state and orchestration. | [E1](#evidence-e1) documented graph tooling; hypothetical framework comparison. Library adoption does not establish agent usefulness or correctness. | Related: [Agent](#term-agen02); Read: [S16](#source-s16), [S03](#source-s03) |
| <a id="term-agen19"></a>[AGEN19](#term-agen19) — LangChain | Framework with model/tool integrations and higher-level agent-building abstractions. | [R7](#evidence-r7) conditional P03/P04 comparison; [A2](#evidence-a2) conditional alternative integration/loop. No adoption is implied. It is not a model, a vector database or mandatory for RAG. | Related: [Agent framework / SDK](#term-agen18) · [LangGraph](#term-agen20); Read: [S23](#source-s23) |
| <a id="term-agen20"></a>[AGEN20](#term-agen20) — LangGraph | Lower-level orchestration framework/runtime for stateful graphs, including deterministic and model-directed steps, persistence and interrupts. | [E1](#evidence-e1) documented graph orchestration reference; not executed or production-verified here. [R7](#evidence-r7) conditional Python P04 trial; [A2](#evidence-a2) conditional LangGraph.js AI21 trial. A graph is not automatically an autonomous agent; durable state does not guarantee exactly-once external effects. | Related: [Workflow / pipeline / DAG](#term-agen01) · [LangChain](#term-agen19) · [Idempotency / deduplication](#term-o09); Read: [S24](#source-s24) |
| <a id="term-agen21"></a>[AGEN21](#term-agen21) — Vercel AI SDK | TypeScript toolkit for model integration, structured generation, tools and agent loops, with separate frontend streaming helpers. | [A2](#evidence-a2) planned AI10 integration candidate and conditional streaming UX; [R7](#evidence-r7) retains the separate Python baseline. No dependency adoption. Closest overlap is LangChain; a tool loop alone does not establish durable workflow execution. | Related: [LangChain](#term-agen19) · [LangGraph](#term-agen20) · [LangSmith](#term-o19); Read: [S26](#source-s26), [S27](#source-s27) |

## Serving, operations and system design

[Back to top](#glossary-top) · [Term index](#term-index) · [Project evidence](#project-evidence) · [Sources](#primary-sources)

Sources: [S10](#source-s10), [S19](#source-s19), [S20](#source-s20), [S21](#source-s21); project-specific examples use [R3](#evidence-r3)/[R6](#evidence-r6)/[A1](#evidence-a1)/[A3](#evidence-a3)/[E3](#evidence-e3).

| ID / term | Meaning | Project example and interview distinction | Related / reading |
| --- | --- | --- | --- |
| <a id="term-o01"></a>[O01](#term-o01) — Prefill / decode | Processing prompt context / generating subsequent tokens. | Conceptual serving analysis: long-input and long-output bottlenecks differ. | Read: [S19](#source-s19), [S20](#source-s20) |
| <a id="term-o02"></a>[O02](#term-o02) — KV cache | Retained attention key/value state reused while decoding compatible context. | Conceptual: distinguish it from response caching, stored conversation and permanent learning. | Related: [Prompt caching / response caching](#term-g17) · [Prefill / decode](#term-o01); Read: [S10](#source-s10) |
| <a id="term-o03"></a>[O03](#term-o03) — TTFT / inter-token latency / throughput | Time to first token / delay between emitted tokens / work per time unit. | Hypothetical serving benchmark. [R1](#evidence-r1) end-to-end latency is not automatically TTFT or tokens/second. | Related: [Latency percentile / population](#term-v19); Read: [S19](#source-s19), [S20](#source-s20) |
| <a id="term-o04"></a>[O04](#term-o04) — Batching / concurrency / backpressure | Grouping work, simultaneous work and controlling admission when capacity is constrained. | [R3](#evidence-r3) bounded native work; [A2](#evidence-a2)/[A3](#evidence-a3) planned queue operations. More concurrent work may increase tail latency or memory pressure. | Related: [Latency percentile / population](#term-v19) · [Memory / state / history](#term-agen08); Read: [S19](#source-s19), [S20](#source-s20) |
| <a id="term-o05"></a>[O05](#term-o05) — CPU/GPU acceleration / offload | Executing model work on different processors or splitting placement. | [R4](#evidence-r4) observed native versus Docker conditions. Docker itself does not imply GPU access or a universal slowdown factor. | Read: [S19](#source-s19), [S20](#source-s20) |
| <a id="term-o06"></a>[O06](#term-o06) — Timeout / deadline / cancellation | A wait limit, an overall time bound and terminating outstanding work. | [R3](#evidence-r3) observed retry-inclusive deadlines. Cancelling a client does not prove remote computation or billing stopped. | Related: [Retry / exponential backoff / jitter](#term-o07) · [Idempotency / deduplication](#term-o09); Read: [S19](#source-s19), [S20](#source-s20) |
| <a id="term-o07"></a>[O07](#term-o07) — Retry / exponential backoff / jitter | Another attempt, growing delays and randomization to avoid synchronized retries. | [R3](#evidence-r3) observed bounded retries/accounting. Retrying can duplicate side effects or charges; failures must remain visible. | Read: [S19](#source-s19), [S20](#source-s20) |
| <a id="term-o08"></a>[O08](#term-o08) — Circuit breaker / dependency stop | Suppressing further calls after dependency-level failure conditions. | [R3](#evidence-r3) observed batch dependency stops. A retry loop and a circuit breaker are different controls. | Read: [S19](#source-s19), [S20](#source-s20) |
| <a id="term-o09"></a>[O09](#term-o09) — Idempotency / deduplication | Repeating a request without additional intended effects / detecting repeated work. | [A3](#evidence-a3) documented operations. Exactly-once effects require more than assuming queue messages arrive once. | Related: [Queue / DLQ / outbox](#term-o10) · [Optimistic concurrency / stale write](#term-o11); Read: [S19](#source-s19), [S20](#source-s20) |
| <a id="term-o10"></a>[O10](#term-o10) — Queue / DLQ / outbox | Deferred delivery, dead-letter handling and a transactional record for later publication. | [A1](#evidence-a1) documented current/future boundaries; [E3](#evidence-e3) reference workflow. A broker acknowledgement is not proof of downstream business completion. | Related: [Workflow / pipeline / DAG](#term-agen01); Read: [S19](#source-s19), [S20](#source-s20) |
| <a id="term-o11"></a>[O11](#term-o11) — Optimistic concurrency / stale write | Version-based conflict detection / an update based on outdated state. | [A1](#evidence-a1) documented correction direction; [E3](#evidence-e3) reference. An approved edit can still be invalid against a newer document version. | Read: [S19](#source-s19), [S20](#source-s20) |
| <a id="term-o12"></a>[O12](#term-o12) — Trace / span / correlation ID | A linked operation graph, one timed unit and a relationship identifier. | [A3](#evidence-a3) observed logging foundation; planned distributed traces. Saved JSON logs alone are not complete distributed tracing. | Read: [S19](#source-s19), [S20](#source-s20) |
| <a id="term-o13"></a>[O13](#term-o13) — Metrics / logs / observability | Aggregated measurements, event records and the ability to understand system behavior from signals. | [A3](#evidence-a3) observed privacy-aware logging; planned operational stack. Avoid raw prompt/document contents in telemetry. | Read: [S19](#source-s19), [S20](#source-s20) |
| <a id="term-o14"></a>[O14](#term-o14) — Experiment tracking / artifact / lineage | Recording a run's parameters/results, retained output and derivation chain. | [R6](#evidence-r6) observed immutable evidence and archive receipts; [E2](#evidence-e2) documented evaluation artifacts. A tracking product is optional. | Related: [Prompt/model/schema version](#term-g18) · [Data lineage / provenance](#term-d14); Read: [S21](#source-s21) |
| <a id="term-o15"></a>[O15](#term-o15) — SLI / SLO / error budget | A measured service indicator, target and permitted reliability shortfall. | Planned workload controls. API spending allowance is not an availability error budget. | Related: [Latency percentile / population](#term-v19) · [Known cost / reservation / unknown charge](#term-v20); Read: [S19](#source-s19), [S20](#source-s20) |
| <a id="term-o16"></a>[O16](#term-o16) — Shadow / canary / A/B release | Observe without acting / limited rollout / compare assigned populations. | Hypothetical deployment: distinguish product experiments from [R2](#evidence-r2)'s offline replay. A canary without evaluable outcomes cannot establish quality. | Read: [S19](#source-s19), [S20](#source-s20) |
| <a id="term-o17"></a>[O17](#term-o17) — Release identity / rollback | Binding deployable behavior to versions and restoring an accepted version. | [R6](#evidence-r6) observed evidence identities; [A1](#evidence-a1) planned deployment. Model, prompt, schema, retrieval index and policy can all affect behavior. | Related: [RAG](#term-rag01); Read: [S19](#source-s19), [S20](#source-s20) |
| <a id="term-o18"></a>[O18](#term-o18) — MLOps / LLMOps | Operational lifecycle practices for ML/LLM systems. | [R2](#evidence-r2)/[R6](#evidence-r6) cover parts of evaluation/reproduction; [A2](#evidence-a2)/[A3](#evidence-a3) plan product operation. These labels do not imply training, deployment or a particular vendor. | Read: [S19](#source-s19), [S20](#source-s20) |
| <a id="term-o19"></a>[O19](#term-o19) — LangSmith | Platform for LLM/agent tracing, debugging and evaluation; usable with different frameworks. | [R7](#evidence-r7) conditional P04/P05 pilot; [A3](#evidence-a3) conditional AI21/AI30 assessment retains AspectLoop's telemetry direction. No LangSmith adoption or enterprise usage is verified here. Traces may contain sensitive inputs; export, redaction and retention need an explicit decision. | Related: [Trace / span / correlation ID](#term-o12) · [Evaluation / benchmark / baseline](#term-v01) · [LangChain](#term-agen19); Read: [S25](#source-s25) |

## Safety and security

[Back to top](#glossary-top) · [Term index](#term-index) · [Project evidence](#project-evidence) · [Sources](#primary-sources)

Sources: [S22](#source-s22); application examples remain bounded by recorded evidence.

| ID / term | Meaning | Project example and interview distinction | Related / reading |
| --- | --- | --- | --- |
| <a id="term-sfty01"></a>[SFTY01](#term-sfty01) — Authentication versus authorization | Establishing identity versus deciding permitted access/actions. | [A1](#evidence-a1) observed session foundation; planned document/tool authorization. Knowing who called does not allow every document or mutation. | Related: [Trust boundary / least privilege](#term-sfty02) · [Proposal versus application](#term-x11); Read: [S22](#source-s22) |
| <a id="term-sfty02"></a>[SFTY02](#term-sfty02) — Trust boundary / least privilege | A transition between differently trusted components; grant only needed capabilities. | [A1](#evidence-a1)/[E3](#evidence-e3) documented read/write boundaries. Retrieved text and tool output are not trusted policy merely because the model sees them. | Read: [S22](#source-s22) |
| <a id="term-sfty03"></a>[SFTY03](#term-sfty03) — Direct/indirect prompt injection | Hostile instructions from a direct request / embedded documents, retrieval or tool content. | [R2](#evidence-r2) observed synthetic controls only. Measure task deviation and blocked effects separately from live model attack success. | Related: [Excessive agency](#term-sfty05) · [System prompt leakage](#term-sfty07); Read: [S22](#source-s22) |
| <a id="term-sfty04"></a>[SFTY04](#term-sfty04) — Sensitive information disclosure / exfiltration | Unintended exposure / transfer of information outside its allowed scope. | [R6](#evidence-r6) privacy exclusions; planned P03/P04 scope markers. Redacting logs does not prove request context is authorized. | Read: [S22](#source-s22) |
| <a id="term-sfty05"></a>[SFTY05](#term-sfty05) — Excessive agency | A system grants more action power than needed or adequately controlled. | [A2](#evidence-a2) planned proposal-only tools. Human approval must be independently enforced at the application boundary. | Related: [Proposal versus application](#term-x11); Read: [S22](#source-s22) |
| <a id="term-sfty06"></a>[SFTY06](#term-sfty06) — Improper output handling | Treating untrusted generated output as safe executable/renderable input. | [R2](#evidence-r2) hostile-string controls. JSON validity does not prevent spreadsheet formulas, HTML execution or unsafe commands at later consumers. | Read: [S22](#source-s22) |
| <a id="term-sfty07"></a>[SFTY07](#term-sfty07) — System prompt leakage | Disclosure of internal instructions or related context. | [R2](#evidence-r2) harmless marker controls. Instructions must not contain credentials; secrecy is not an authorization boundary. | Related: [Authentication versus authorization](#term-sfty01); Read: [S22](#source-s22) |
| <a id="term-sfty08"></a>[SFTY08](#term-sfty08) — Data/model poisoning | Manipulating data or artifacts to influence system behavior improperly. | Planned reviewed feedback/reference lifecycle. Automatically learning from unreviewed corrections invites integrity problems. | Read: [S22](#source-s22) |
| <a id="term-sfty09"></a>[SFTY09](#term-sfty09) — Vector/embedding weakness | Retrieval/index flaws such as unsafe scope, relevance manipulation or stale evidence. | Planned P03: test access filtering, deletion and relevance, not just vector similarity. | Related: [RAG](#term-rag01); Read: [S22](#source-s22) |
| <a id="term-sfty10"></a>[SFTY10](#term-sfty10) — Unbounded consumption | Uncontrolled use of calls, tokens, time, storage or money. | [R3](#evidence-r3) observed limits/holds; [A2](#evidence-a2) planned tools need whole-workflow budgets. Per-call limits alone do not bound a loop. | Related: [Workflow / pipeline / DAG](#term-agen01); Read: [S22](#source-s22) |
| <a id="term-sfty11"></a>[SFTY11](#term-sfty11) — PII / minimization / retention | Personal information, restricting collected data and governing how long it remains. | [R6](#evidence-r6) neutral public evidence; [A3](#evidence-a3) redaction. Audit needs do not justify retaining every raw prompt forever. | Read: [S22](#source-s22) |
| <a id="term-sfty12"></a>[SFTY12](#term-sfty12) — Supply chain / model provenance | Dependencies and artifacts whose origin/integrity affect behavior. | [R6](#evidence-r6) observed digests and lockfiles. Open weights, open source code, license rights and trusted provenance are separate questions. | Related: [Data lineage / provenance](#term-d14) · [Parameters / weights](#term-f08); Read: [S22](#source-s22) |

## Project evidence

[Back to top](#glossary-top) · [Term index](#term-index) · [Project evidence](#project-evidence) · [Sources](#primary-sources)

Local examples were reviewed on 2026-11-07. Their measurement dates remain those
of the linked reports. Planned examples are not promoted by being in this table.

| ID | Evidence and status | Terms citing this evidence |
| --- | --- | --- |
| <a id="evidence-r1"></a>[R1](#evidence-r1) | **Observed rd_ai:** [contract](extraction-contract.md), [evaluation rules](evaluation.md), [authoritative schema](../../schemas/purchase-order-extraction.v1.schema.json), [scorer](../../src/extraction_service/evaluation/scoring.py). | [D01](#term-d01), [D03](#term-d03), [D04](#term-d04), [D14](#term-d14), [F04](#term-f04), [G12](#term-g12), [O03](#term-o03), [V06](#term-v06), [V07](#term-v07), [V09](#term-v09), [V19](#term-v19), [X03](#term-x03), [X07](#term-x07) |
| <a id="evidence-r2"></a>[R2](#evidence-r2) | **Observed rd_ai:** [P01 report](../reports/P01-evaluation-protocols.md), [protocol guide](../guides/evaluation-protocols.md), [paired analysis](../../src/extraction_service/evaluation/comparison.py), [exposure inventory](../../config/evaluation/exposure-v1.json). | [D05](#term-d05), [D06](#term-d06), [D07](#term-d07), [D08](#term-d08), [D12](#term-d12), [D13](#term-d13), [G16](#term-g16), [G18](#term-g18), [O16](#term-o16), [O18](#term-o18), [SFTY03](#term-sfty03), [SFTY06](#term-sfty06), [SFTY07](#term-sfty07), [T18](#term-t18), [V01](#term-v01), [V02](#term-v02), [V03](#term-v03), [V08](#term-v08), [V10](#term-v10), [V12](#term-v12), [V13](#term-v13), [V18](#term-v18), [V21](#term-v21), [X09](#term-x09) |
| <a id="evidence-r3"></a>[R3](#evidence-r3) | **Observed rd_ai:** [coordinator/accounting](execution-coordinator.md), [model-adapter ownership](model-adapters.md), [runtime validation](runtime-validation.md). | [AGEN01](#term-agen01), [AGEN03](#term-agen03), [AGEN16](#term-agen16), [F01](#term-f01), [G09](#term-g09), [G15](#term-g15), [O04](#term-o04), [O06](#term-o06), [O07](#term-o07), [O08](#term-o08), [SFTY10](#term-sfty10), [T15](#term-t15), [V20](#term-v20) |
| <a id="evidence-r4"></a>[R4](#evidence-r4) | **Recorded rd_ai experiments:** [revised v1](../reports/revised-v1-baseline-results.md), [v2 continuation](../reports/v2-continuation-results.md), [runtime comparison](../reports/local-runtime-comparison.md), [output allowance](../reports/output-allowance-experiment.md), [large context](../reports/native-large-context.md). | [F05](#term-f05), [F06](#term-f06), [F08](#term-f08), [F10](#term-f10), [F12](#term-f12), [G01](#term-g01), [G02](#term-g02), [G03](#term-g03), [G05](#term-g05), [G06](#term-g06), [G11](#term-g11), [G15](#term-g15), [O05](#term-o05), [T07](#term-t07), [T08](#term-t08), [T16](#term-t16), [V11](#term-v11) |
| <a id="evidence-r5"></a>[R5](#evidence-r5) | **Recorded rd_ai support/examples:** [source support](../guides/source-support.md), [prompt resources](../guides/prompt-resources.md), [identifier correction](../reports/identifier-correction.md), [header/line split](../reports/gemma-header-lines.md). | [AGEN10](#term-agen10), [D02](#term-d02), [G08](#term-g08), [G10](#term-g10), [G13](#term-g13), [T17](#term-t17), [V11](#term-v11), [X02](#term-x02), [X04](#term-x04), [X06](#term-x06) |
| <a id="evidence-r6"></a>[R6](#evidence-r6) | **Observed rd_ai preservation:** [reproduction](../guides/reproducing-results.md), [archival](../guides/archiving-results.md), [P00/S08 migration](../reports/runtime-name-migration.md). | [D14](#term-d14), [D15](#term-d15), [G18](#term-g18), [O14](#term-o14), [O17](#term-o17), [O18](#term-o18), [SFTY04](#term-sfty04), [SFTY11](#term-sfty11), [SFTY12](#term-sfty12) |
| <a id="evidence-r7"></a>[R7](#evidence-r7) | **Planned rd_ai:** [P02–P05 roadmap](../roadmap.md), including [framework/SDK proposals](../roadmap.md#framework-and-sdk-experiments); [cross-project topic mapping](ai-engineer-topic-mapping.md). | [AGEN19](#term-agen19), [AGEN20](#term-agen20), [AGEN21](#term-agen21), [O19](#term-o19) |
| <a id="evidence-a1"></a>[A1](#evidence-a1) | **AspectLoop documented architecture/current state:** separate repository `docs/general-plan.md`, `docs/data-and-recovery.md`, `docs/browser-session.md`; verify each feature's status before claiming completion. | [AGEN08](#term-agen08), [AGEN09](#term-agen09), [D14](#term-d14), [O10](#term-o10), [O11](#term-o11), [O17](#term-o17), [SFTY01](#term-sfty01), [SFTY02](#term-sfty02), [X12](#term-x12) |
| <a id="evidence-a2"></a>[A2](#evidence-a2) | **AspectLoop planned AI:** `docs/general-plan.md`, AI00/AI10/AI11/AI12/AI20/AI21/AI30, including the 2026-11-07 framework/SDK proposals; current foundation and planned capabilities are distinct. | [AGEN02](#term-agen02), [AGEN19](#term-agen19), [AGEN20](#term-agen20), [AGEN21](#term-agen21), [F12](#term-f12), [G13](#term-g13), [O04](#term-o04), [O18](#term-o18), [SFTY05](#term-sfty05), [SFTY10](#term-sfty10), [T15](#term-t15), [X01](#term-x01), [X10](#term-x10), [X11](#term-x11) |
| <a id="evidence-a3"></a>[A3](#evidence-a3) | **AspectLoop observed logging foundation/planned monitoring and tracing pilots:** `docs/logging-and-privacy.md`; M10/M11 and conditional AI21/AI30 LangSmith assessment in `docs/general-plan.md`. | [O04](#term-o04), [O09](#term-o09), [O12](#term-o12), [O13](#term-o13), [O18](#term-o18), [O19](#term-o19), [SFTY11](#term-sfty11) |
| <a id="evidence-e1"></a>[E1](#evidence-e1) | **Elemica documented reference only:** staged document preparation/extraction and graph-based orchestration. This is a generic architectural observation, not a production verification claim. | [AGEN01](#term-agen01), [AGEN18](#term-agen18), [AGEN20](#term-agen20), [X01](#term-x01) |
| <a id="evidence-e2"></a>[E2](#evidence-e2) | **Elemica documented reference only:** separate reference-versus-generated evaluation and performance measurements. Evaluation rules may differ from rd_ai's exact scorer. | [O14](#term-o14) |
| <a id="evidence-e3"></a>[E3](#evidence-e3) | **Elemica documented reference only:** correction review, separate read/write operations, draft/submit states and source artifacts. Product behavior is not inferred from file names alone. | [O10](#term-o10), [O11](#term-o11), [SFTY02](#term-sfty02), [X10](#term-x10), [X11](#term-x11), [X12](#term-x12) |

Exact enterprise code locators are retained only in ignored local
`data/private/reference-notes/ai-ml-glossary-elemica.md`. That companion is
optional for reading the public glossary. No proprietary source, prompt,
business payload, customer data or credentials are reproduced here. Elemica is
a research reference, not an affiliation or dependency of either project.

## LangChain, LangGraph and LangSmith

[Back to top](#glossary-top) · [Term index](#term-index) · [Project evidence](#project-evidence)

| Name | Main responsibility | Interview distinction |
| --- | --- | --- |
| [LangChain](#term-agen19) | Compose model/tool integrations and higher-level agent behavior. | A framework around models; it does not supply model weights or guarantee correct outcomes. |
| [LangGraph](#term-agen20) | Explicit state and control flow, persistence, pauses and continuation. | Can orchestrate workflows and agents, and can be used without LangChain. Authorization and idempotency still need application enforcement. |
| [LangSmith](#term-o19) | Observe, debug and evaluate application behavior. | Can instrument other frameworks; neither a required LangGraph component nor an automatic replacement for infrastructure telemetry. |

A possible future comparison would implement the same bounded document-review
workflow manually and with a selected framework, then compare quality, failures,
calls, latency and maintenance effort. The enterprise reference demonstrates
documented graph orchestration only; it does not establish adoption in the two
learning projects. Any telemetry trial needs explicit data handling and access
decisions. No package installation, model run or hosted service setup follows
from adding these terms. See [S23](#source-s23), [S24](#source-s24) and [S25](#source-s25).

### Relationship to Vercel AI SDK

[Vercel AI SDK](#term-agen21) overlaps most with [LangChain](#term-agen19):
both provide model integrations and tool/agent-loop abstractions. AI SDK Core
supports generation, structured output and tool calls; AI SDK UI adds frontend
streaming and state helpers. It can be used outside Next.js and Vercel hosting.
Its tool loop and an explicit durable [LangGraph](#term-agen20) workflow have
different responsibilities; choose orchestration based on persistence,
branching and pause/resume requirements. SDK and framework are overlapping
product labels, not mutually exclusive architectural layers. See [S26](#source-s26).

[LangSmith](#term-o19) can trace AI SDK applications without adopting LangChain;
the official integration is documented in [S27](#source-s27). The proposed
AspectLoop trial compares TypeScript model integration inside existing
service boundaries, with UI streaming evaluated separately. rd_ai's Python
implementation does not need a language migration to exercise these concepts.
These are planned conditional comparisons, not installed dependencies or configured
telemetry exports. See [R7](#evidence-r7).

Project proposals (planned comparisons, not adoption decisions): retain
rd_ai's existing Python adapters and execution/accounting controls for fixed
extraction runs. A bounded P04 LangGraph comparison would test whether persisted
review state, interrupts and recovery justify its added complexity. For
AspectLoop's planned TypeScript extraction service, evaluate AI SDK Core behind
the provider boundary first; consider LangGraph.js separately for a correction
workflow requiring explicit resumable state. Application authorization,
idempotency, validation and budget controls remain application responsibilities.
Framework adoption alone does not improve extraction accuracy. See
[rd_ai framework/SDK scope](../roadmap.md#framework-and-sdk-experiments) and
[AspectLoop topic mapping](ai-engineer-topic-mapping.md).

## Interview practice

[Back to top](#glossary-top) · [Term index](#term-index) · [Project evidence](#project-evidence) · [Sources](#primary-sources)

These are author-created study questions based on the projects, not sourced
interview transcripts. Answer with definition → trade-off → concrete evidence
→ limitation. Say "planned" or "conceptual" where that is the honest status.

| Question | A strong answer should include |
| --- | --- |
| Why was a 100% provider score insufficient proof of reliability? | [R1](#evidence-r1)/[R2](#evidence-r2): reused gold10, exact matching population, no unseen-layout claim and preservation of unlabeled cases. |
| Why did more output tokens not solve local extraction? | [G02](#term-g02)/[G03](#term-g03) and [R4](#evidence-r4): output truncation differs from incorrect row selection; latency and extra rows can grow. |
| How would you compare v1 and v2 fairly? | [V10](#term-v10)/[V11](#term-v11): fixed membership, declared control differences, failures, primary denominators, 46 gains and 12 regressions in the recorded P01 example. |
| When would you use RAG rather than fine-tuning? | [RAG17](#term-rag17): changing authoritative knowledge versus behavior adaptation, separate evals and reviewed data; no blanket winner. |
| How do you stop a model from submitting an unauthorized change? | [AGEN04](#term-agen04)/[SFTY05](#term-sfty05): trusted principal, validated tool arguments, separate approval/apply command, version checks and denied positive/negative cases. |
| Does loading a skill make Gemma an agent? | [AGEN03](#term-agen03)/[AGEN10](#term-agen10): resource loading, state, tools and control loop belong to a harness; instructions do not update weights or grant effects. |
| How do you evaluate an abstaining system? | [X09](#term-x09)/[V15](#term-v15): review coverage, error among accepted decisions, false abstentions and unusable outputs; no hidden denominator shrinkage. |
| Why is schema validation insufficient? | [R1](#evidence-r1)/[X07](#term-x07): a complete correctly typed catalog row can still be unrequested; business/source evidence is separate. |
| How do you measure latency and cost? | [V19](#term-v19)/[V20](#term-v20)/[O03](#term-o03): populations, retries, tail latency, known charges/holds, local hardware exclusions and reviewer effort. |
| What would you reuse from the enterprise reference? | [E1](#evidence-e1)–[E3](#evidence-e3): general orchestration/evaluation/approval patterns after comparing contracts; no copied proprietary implementation or invented AI equivalence. |
| What happens after a timed-out model or tool call? | [O06](#term-o06)/[O07](#term-o07)/[O09](#term-o09): cancellation uncertainty, durable attempt state, duplicate effects, billing holds and bounded retries. |
| How do you know retrieval helped? | [V17](#term-v17)/[RAG13](#term-rag13), [RAG14](#term-rag14), [RAG15](#term-rag15): reviewed relevance, answer support/citations, ablation and scope isolation; final accuracy alone cannot isolate retrieval benefit. |

## Primary sources

[Back to top](#glossary-top) · [Term index](#term-index) · [Project evidence](#project-evidence) · [Sources](#primary-sources)

Terminology/reference review date for this initial edition: **2026-11-07**.
These are learning references, not a claim that a library is installed or that
its latest API/version has been adopted. Recheck versioned specifications before
implementation. Stable concepts and volatile implementation details are separate.

| ID | Primary reference | Use | Terms citing this reference |
| --- | --- | --- | --- |
| <a id="source-s01"></a>[S01](#source-s01) | [Google ML glossary](https://developers.google.com/machine-learning/glossary) | Foundational terminology and further reading. | [F01](#term-f01), [F02](#term-f02), [F03](#term-f03), [F04](#term-f04), [F05](#term-f05), [F06](#term-f06), [F07](#term-f07), [F08](#term-f08), [F09](#term-f09), [F10](#term-f10), [F11](#term-f11), [F12](#term-f12), [T01](#term-t01), [T02](#term-t02), [T03](#term-t03), [T04](#term-t04), [T05](#term-t05), [T06](#term-t06), [T07](#term-t07), [T08](#term-t08), [T09](#term-t09), [T10](#term-t10), [T12](#term-t12), [T13](#term-t13), [T14](#term-t14), [T15](#term-t15), [T17](#term-t17) |
| <a id="source-s02"></a>[S02](#source-s02) | [AI Engineer roadmap](https://roadmap.sh/ai-engineer) and [publisher topic index](https://github.com/nilbuild/developer-roadmap/tree/master/roadmaps/ai-engineer/content) | Topic scope, not a certification or vendor checklist. | [F01](#term-f01), [F02](#term-f02), [F03](#term-f03), [F04](#term-f04), [F05](#term-f05), [F06](#term-f06), [F07](#term-f07), [F08](#term-f08), [F09](#term-f09), [F10](#term-f10), [F11](#term-f11), [F12](#term-f12) |
| <a id="source-s03"></a>[S03](#source-s03) | [Anthropic context engineering](https://www.anthropic.com/research/effective-context-engineering-for-ai-agents) | Context selection, retention and compaction. | [AGEN01](#term-agen01), [AGEN02](#term-agen02), [AGEN03](#term-agen03), [AGEN04](#term-agen04), [AGEN05](#term-agen05), [AGEN06](#term-agen06), [AGEN07](#term-agen07), [AGEN08](#term-agen08), [AGEN09](#term-agen09), [AGEN10](#term-agen10), [AGEN16](#term-agen16), [AGEN17](#term-agen17), [AGEN18](#term-agen18), [G13](#term-g13), [G14](#term-g14) |
| <a id="source-s04"></a>[S04](#source-s04) | [PyTorch autograd](https://docs.pytorch.org/tutorials/beginner/basics/autogradqs_tutorial.html) | Gradients and training mechanics. | [T01](#term-t01), [T02](#term-t02), [T03](#term-t03), [T04](#term-t04), [T05](#term-t05), [T06](#term-t06), [T07](#term-t07), [T08](#term-t08), [T09](#term-t09), [T10](#term-t10), [T12](#term-t12), [T13](#term-t13), [T14](#term-t14), [T15](#term-t15), [T17](#term-t17) |
| <a id="source-s05"></a>[S05](#source-s05) | [Hugging Face LoRA](https://huggingface.co/docs/peft/main/en/conceptual_guides/lora) | Parameter-efficient adaptation. | [T11](#term-t11) |
| <a id="source-s06"></a>[S06](#source-s06) | [Hugging Face quantization](https://huggingface.co/docs/transformers/main/en/quantization/overview) | Precision/resource trade-offs. | [T16](#term-t16) |
| <a id="source-s07"></a>[S07](#source-s07) | [Google dataset splits](https://developers.google.com/machine-learning/crash-course/overfitting/dividing-datasets) | Development/test roles and repeated use. | [D01](#term-d01), [D02](#term-d02), [D03](#term-d03), [D04](#term-d04), [D05](#term-d05), [D06](#term-d06), [D07](#term-d07), [D08](#term-d08), [D09](#term-d09), [D10](#term-d10), [D11](#term-d11), [D12](#term-d12), [D13](#term-d13), [D14](#term-d14), [D15](#term-d15), [D16](#term-d16) |
| <a id="source-s08"></a>[S08](#source-s08) | [Google overfitting](https://developers.google.com/machine-learning/crash-course/overfitting/overfitting) | Generalization limits. | [D01](#term-d01), [D02](#term-d02), [D03](#term-d03), [D04](#term-d04), [D05](#term-d05), [D06](#term-d06), [D07](#term-d07), [D08](#term-d08), [D09](#term-d09), [D10](#term-d10), [D11](#term-d11), [D12](#term-d12), [D13](#term-d13), [D14](#term-d14), [D15](#term-d15), [D16](#term-d16), [T18](#term-t18) |
| <a id="source-s09"></a>[S09](#source-s09) | [Hugging Face Tokenizers](https://huggingface.co/docs/tokenizers/index) | Tokenization terminology. | [G01](#term-g01), [G02](#term-g02), [G03](#term-g03), [G04](#term-g04), [G05](#term-g05), [G06](#term-g06), [G07](#term-g07), [G08](#term-g08), [G09](#term-g09), [G10](#term-g10), [G11](#term-g11), [G12](#term-g12), [G15](#term-g15), [G17](#term-g17), [G18](#term-g18) |
| <a id="source-s10"></a>[S10](#source-s10) | [Hugging Face generation](https://huggingface.co/docs/transformers/main/en/llm_tutorial) and [KV cache](https://huggingface.co/docs/transformers/main/en/kv_cache) | Generation and inference mechanics. | [G01](#term-g01), [G02](#term-g02), [G03](#term-g03), [G04](#term-g04), [G05](#term-g05), [G06](#term-g06), [G07](#term-g07), [G08](#term-g08), [G09](#term-g09), [G10](#term-g10), [G11](#term-g11), [G12](#term-g12), [G15](#term-g15), [G17](#term-g17), [G18](#term-g18), [O02](#term-o02) |
| <a id="source-s11"></a>[S11](#source-s11) | [Google classification metrics](https://developers.google.com/machine-learning/crash-course/classification/accuracy-precision-recall) | Precision, recall and denominators. | [V01](#term-v01), [V02](#term-v02), [V03](#term-v03), [V04](#term-v04), [V05](#term-v05), [V11](#term-v11), [V12](#term-v12), [V13](#term-v13), [V15](#term-v15), [V16](#term-v16), [V17](#term-v17), [V18](#term-v18), [V21](#term-v21) |
| <a id="source-s12"></a>[S12](#source-s12) | [OpenAI eval guidance](https://developers.openai.com/api/docs/guides/evals) | Task-specific evaluation design; no Evals API adoption implied. | [V01](#term-v01), [V02](#term-v02), [V03](#term-v03), [V04](#term-v04), [V05](#term-v05), [V11](#term-v11), [V12](#term-v12), [V13](#term-v13), [V14](#term-v14), [V15](#term-v15), [V16](#term-v16), [V17](#term-v17), [V18](#term-v18), [V21](#term-v21) |
| <a id="source-s13"></a>[S13](#source-s13) | [rd_ai evaluation contract](evaluation.md) | Exact local rules supersede generic metric assumptions for these results. | [V06](#term-v06), [V07](#term-v07), [V08](#term-v08), [V09](#term-v09), [V10](#term-v10), [V19](#term-v19), [V20](#term-v20), [X01](#term-x01), [X02](#term-x02), [X03](#term-x03), [X04](#term-x04), [X05](#term-x05), [X06](#term-x06), [X07](#term-x07), [X08](#term-x08), [X09](#term-x09), [X10](#term-x10), [X11](#term-x11), [X12](#term-x12) |
| <a id="source-s14"></a>[S14](#source-s14) | [Original RAG paper](https://arxiv.org/abs/2005.11401) | Retrieval plus generation; not the only modern RAG design. | [RAG01](#term-rag01), [RAG02](#term-rag02), [RAG03](#term-rag03), [RAG04](#term-rag04), [RAG05](#term-rag05), [RAG06](#term-rag06), [RAG07](#term-rag07), [RAG08](#term-rag08), [RAG09](#term-rag09), [RAG10](#term-rag10), [RAG11](#term-rag11), [RAG12](#term-rag12), [RAG13](#term-rag13), [RAG14](#term-rag14), [RAG15](#term-rag15), [RAG16](#term-rag16), [RAG17](#term-rag17) |
| <a id="source-s15"></a>[S15](#source-s15) | [Sentence Transformers retrieve/rerank](https://www.sbert.net/examples/sentence_transformer/applications/retrieve_rerank/README.html) | Retrieval and reranking responsibilities. | [RAG01](#term-rag01), [RAG02](#term-rag02), [RAG03](#term-rag03), [RAG04](#term-rag04), [RAG05](#term-rag05), [RAG06](#term-rag06), [RAG07](#term-rag07), [RAG08](#term-rag08), [RAG09](#term-rag09), [RAG10](#term-rag10), [RAG11](#term-rag11), [RAG12](#term-rag12), [RAG13](#term-rag13), [RAG14](#term-rag14), [RAG15](#term-rag15), [RAG16](#term-rag16), [RAG17](#term-rag17) |
| <a id="source-s16"></a>[S16](#source-s16) | [Anthropic effective agents](https://www.anthropic.com/research/building-effective-agents) | Workflow/agent distinctions and bounded architecture patterns. | [AGEN01](#term-agen01), [AGEN02](#term-agen02), [AGEN03](#term-agen03), [AGEN04](#term-agen04), [AGEN05](#term-agen05), [AGEN06](#term-agen06), [AGEN07](#term-agen07), [AGEN08](#term-agen08), [AGEN09](#term-agen09), [AGEN10](#term-agen10), [AGEN16](#term-agen16), [AGEN17](#term-agen17), [AGEN18](#term-agen18) |
| <a id="source-s17"></a>[S17](#source-s17) | [MCP introduction](https://modelcontextprotocol.io/docs/getting-started/intro) | Protocol architecture; version-specific implementation needs a fresh check. | [AGEN11](#term-agen11), [AGEN12](#term-agen12), [AGEN13](#term-agen13), [AGEN14](#term-agen14) |
| <a id="source-s18"></a>[S18](#source-s18) | [A2A official documentation](https://a2a-protocol.org/latest/) | Agent interoperability versus tool/context integration. | [AGEN15](#term-agen15) |
| <a id="source-s19"></a>[S19](#source-s19) | [vLLM metrics](https://docs.vllm.ai/en/latest/design/metrics/) | Serving measurements; vLLM is not an adopted dependency. | [O01](#term-o01), [O03](#term-o03), [O04](#term-o04), [O05](#term-o05), [O06](#term-o06), [O07](#term-o07), [O08](#term-o08), [O09](#term-o09), [O10](#term-o10), [O11](#term-o11), [O12](#term-o12), [O13](#term-o13), [O15](#term-o15), [O16](#term-o16), [O17](#term-o17), [O18](#term-o18), [V19](#term-v19) |
| <a id="source-s20"></a>[S20](#source-s20) | [OpenTelemetry signals](https://opentelemetry.io/docs/concepts/signals/) | Logs, metrics and traces. | [O01](#term-o01), [O03](#term-o03), [O04](#term-o04), [O05](#term-o05), [O06](#term-o06), [O07](#term-o07), [O08](#term-o08), [O09](#term-o09), [O10](#term-o10), [O11](#term-o11), [O12](#term-o12), [O13](#term-o13), [O15](#term-o15), [O16](#term-o16), [O17](#term-o17), [O18](#term-o18) |
| <a id="source-s21"></a>[S21](#source-s21) | [MLflow tracking](https://mlflow.org/docs/latest/ml/tracking/) | Run/artifact tracking concepts; MLflow is not an adopted dependency. | [O14](#term-o14) |
| <a id="source-s22"></a>[S22](#source-s22) | [OWASP LLM Top 10, 2025](https://genai.owasp.org/llm-top-10/) | Risk vocabulary and exercise mapping, not security certification. | [G16](#term-g16), [SFTY01](#term-sfty01), [SFTY02](#term-sfty02), [SFTY03](#term-sfty03), [SFTY04](#term-sfty04), [SFTY05](#term-sfty05), [SFTY06](#term-sfty06), [SFTY07](#term-sfty07), [SFTY08](#term-sfty08), [SFTY09](#term-sfty09), [SFTY10](#term-sfty10), [SFTY11](#term-sfty11), [SFTY12](#term-sfty12) |
| <a id="source-s23"></a>[S23](#source-s23) | [LangChain overview](https://docs.langchain.com/oss/python/langchain/overview) | Agent/model/tool abstractions; reviewed 2026-11-07, no dependency adoption. | [AGEN19](#term-agen19) |
| <a id="source-s24"></a>[S24](#source-s24) | [LangGraph overview](https://docs.langchain.com/oss/python/langgraph/overview) | Stateful orchestration, persistence and interrupts; reviewed 2026-11-07. | [AGEN20](#term-agen20) |
| <a id="source-s25"></a>[S25](#source-s25) | [LangSmith observability](https://docs.langchain.com/langsmith/observability) | Cross-framework tracing/evaluation; reviewed 2026-11-07, no account or export configured. | [O19](#term-o19) |
| <a id="source-s26"></a>[S26](#source-s26) | [AI SDK Core](https://ai-sdk.dev/docs/ai-sdk-core/overview), [agents](https://ai-sdk.dev/docs/agents/overview), [AI SDK UI](https://ai-sdk.dev/docs/ai-sdk-ui/overview) | TypeScript model integration, agent loops and frontend streaming; reviewed 2026-11-07. | [AGEN21](#term-agen21) |
| <a id="source-s27"></a>[S27](#source-s27) | [Trace Vercel AI SDK with LangSmith](https://docs.langchain.com/langsmith/trace-with-vercel-ai-sdk) | Framework-independent tracing integration; reviewed 2026-11-07, no export configured. | [AGEN21](#term-agen21), [O19](#term-o19) |

## Maintenance procedure

[Back to top](#glossary-top) · [Term index](#term-index) · [Project evidence](#project-evidence) · [Sources](#primary-sources)

1. Preserve term/evidence/source anchors and bidirectional references. Add new
   terms to the alphabetical index, link relevant evidence/readings and refresh
   the evidence/source backlinks; verify every fragment target after edits.
2. During relevant implementation, research, experiment review or interview
   preparation, inspect affected entries rather than copying a parallel glossary.
3. Add/update the definition, exact project status, evidence locator and one
   useful distinction. Preserve IDs, historical dates and measured populations.
4. Verify unstable vendor/protocol claims against primary sources; date material
   reviews. Never add "industry standard" or "commonly asked" without evidence.
5. Record newly exercised capability only after actual verification. A plan,
   dependency import or model name does not establish coverage. An unrun method
   remains conceptual/hypothetical/planned, even when interview-relevant.
6. Keep private enterprise locators in the ignored companion. Treat reference
   repositories as read-only unless the user explicitly changes their scope.
   Do not create a hard dependency on access to proprietary repositories.
7. Update the revision history and project evidence when semantics/status change.
   Small typo/link repairs need not create a new conceptual version. Keep the
   navigation link and update guidance current.
8. If the canonical checkout is unavailable or outside authorized write scope,
   record the proposed glossary update in the task handoff. Do not silently
   create another canonical copy or mutate a read-only reference project.

Updates are event-driven parts of future authorized work, not an unattended
background job or a promise of automatic upstream monitoring. No model calls,
dependency installs or new experiments are authorized by maintaining definitions.

| Version | Date | Change |
| --- | --- | --- |
| 1.0 | 2026-11-07 | Initial living glossary, project evidence/limitations, industry protocol and serving vocabulary, interview practice and cross-project update procedure. |
| 1.1 | 2026-11-07 | Add alphabetical term/alias index, stable term/evidence/source anchors, related-term links, per-term readings and evidence/source backlinks. |
| 1.2 | 2026-11-07 | Add LangChain, LangGraph and LangSmith definitions, project distinctions, official sources and bidirectional navigation. |
| 1.3 | 2026-11-07 | Explain Vercel AI SDK overlap, UI responsibilities and LangSmith interoperability with official sources. |
| 1.4 | 2026-11-07 | Synchronize conditional framework/SDK proposals with rd_ai P03-P05 and AspectLoop AI10/AI21/AI30; retain unadopted status and update project evidence backlinks. |
