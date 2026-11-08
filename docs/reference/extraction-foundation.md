# Extraction foundation — historical HW-01 flow

- Version: **1.0**.
- Documented: **2026-11-08** from the implemented workflow and saved reports.
- Status: **Inherited, exercised foundation**; later milestone flows have their own status.

HW-01 established the extraction, execution and evaluation foundation now used
by the document-intelligence R&D project. This diagram describes the completed
foundation as it evolved through the extraction experiments, not just its first
smoke run. P00 subsequently moved the application to the repository root.
Historical run IDs, configurations and evidence retain their original identities.

## Extraction and evaluation flow

```mermaid
flowchart TD
    subgraph Inputs["1. Frozen inputs and experiment controls"]
        SRC["30 approved neutral source texts"]
        CFG["Selected model, prompt v1/v2, sampling and execution profile"]
        SCHEMA["Authoritative PO v1 JSON Schema"]
        GOLD["10 human-approved gold POs: evaluator only"]
        SRC --> PREF["Offline preflight: verify selections, hashes and contracts"]
        CFG --> PREF
        SCHEMA --> PREF
    end

    subgraph Execution["2. Application-controlled extraction"]
        PREF --> SETUP["Application setup: own clients; inject adapters and identities"]
        SETUP --> RUN["Unique run manifest and selected jobs"]
        RUN --> ADMIT{"Dependency, deadline, context and budget admission"}
        ADMIT -->|Blocked| STOP["Explicit failed or not-attempted outcome"]
        ADMIT -->|Admitted| PAY{"Paid request?"}
        PAY -->|Yes| RES["Durable cumulative ledger reservation"]
        PAY -->|No| CALL["One physical adapter request"]
        RES --> CALL
        CALL --> LOCAL["Gemma through native Ollama"]
        CALL --> CLOUD["Selected Gemini through OpenRouter"]
        LOCAL --> RAW["Checkpoint exact response or transport failure and usage"]
        CLOUD --> RAW
        RAW --> BILL["Reconcile billed cost; preserve unknown-charge holds"]
        BILL --> POLICY{"Classify response and apply bounded policy"}
        POLICY -->|Retryable transport failure| RETRY["Bounded retry and backoff"]
        RETRY --> ADMIT
        POLICY -->|Completed response| VALID["Parse JSON and validate against the same PO schema"]
        SCHEMA --> VALID
        POLICY -->|Refused, truncated, late or terminal failure| FAIL["Retain explicit failure and raw evidence"]
        VALID -->|Valid| OK["Structurally valid extraction; factual correctness unproven"]
        VALID -->|Invalid, correction available| FIX["One correction: original source, invalid output and validation issues"]
        FIX --> ADMIT
        VALID -->|Invalid, correction exhausted| FAIL
        STOP --> SAVE["Persist terminal input record, attempts, identities and hashes"]
        FAIL --> SAVE
        OK --> SAVE
        SAVE -->|Next selected job| ADMIT
        SAVE --> DONE["Finalize selected-job summary; checked export"]
    end

    subgraph Evaluation["3. Offline evaluation and preservation: no inference"]
        DONE --> VERIFY["Verify saved records, manifests and matrix membership"]
        VERIFY --> FACT["Gold10: exact header and positional line-field comparison"]
        GOLD --> FACT
        VERIFY --> OPS["All30: validity, failures, latency, tokens and cost"]
        FACT --> REPORT["Paired variant reports with explicit populations and limits"]
        OPS --> REPORT
        REPORT --> ARCH["Garage archival, full-object verification and restore"]
        ARCH --> REPRO["Reproduce reports from saved evidence without models"]
    end
```

The two model boxes are **alternative selected backends**, not automatic
fallback or mandatory calls to both. Python runs in Docker; native Ollama owns
local inference. Early Docker-Ollama diagnostics remain historical evidence,
but Docker Ollama is not the selected local runtime for the inherited matrix.
Other screening candidates and optional local trials are documented separately.

Retries and the single schema correction are available capabilities, not claims
that every run used them. The final 240-observation matrix used neither transport
retries nor schema corrections. Provider inference required concrete approval;
the diagram does not authorize new calls. Admission failures preserve their
actual status and reason rather than inventing a physical attempt.

Gold answers never enter generation messages. Structural schema validity does
not establish source support or accuracy. Factual scores use gold10 only; the
remaining twenty documents contribute operational results, not inferred labels.
Gold10 was reused during development and is not an independent holdout.

## How this foundation feeds later milestones

```mermaid
flowchart TD
    F["Exercised HW-01 foundation"] --> EX["Frozen schema, corpus, prompts and saved extraction records"]
    F --> RT["Injected adapters, admission, deadlines, retries and durable accounting"]
    F --> EV["Independent offline scoring and verified archive/reproduction"]
    EX --> P00["P00: consolidate one R&D application; preserve evidence identities"]
    RT --> P00
    EV --> P00
    P00 --> P01["P01 exercised: versioned evaluation protocols and paired controls"]
    P01 --> P02["P02 exercised slice: exact field locations and inherited support linkage"]
    P01 --> P03["P03 planned: authorized reference retrieval and generated answers"]
    P02 --> P03
    P03 --> P04["P04 planned: human-reviewed proposals and bounded orchestration"]
```

These arrows indicate inherited capabilities, not automatic milestone approval.
P02's executed text-provenance slice does not imply all possible workbook or
semantic studies were completed. P03 retrieves a separate reference collection:
saved predictions, gold labels and diagnostic verdicts do not become its answer
corpus. Existing PO-specific execution assumptions must be adapted explicitly
before handling new answer jobs; reusing controls does not mean reusing PO output
objects for every task.

## Detailed evidence and related flows

- [Consolidated results and complete 240-observation matrix](../../REPORT.md).
- [Execution ownership, checkpointing and persistence](../guides/running-extractions.md#flow-and-ownership).
- [Coordinator retry, correction and accounting policy](execution-coordinator.md#request-and-correction-sequence).
- [Exact scoring and operational metric populations](evaluation.md).
- [Archive and restore workflow](../guides/archiving-results.md).
- [P00 consolidation record](../reports/P00-consolidation.md).
- [P01 executed flow](../reports/P01-evaluation-protocols.md#executed-flow).
- [P02 executed flow](../reports/P02-source-provenance.md#executed-flow).
- [P03 planned flow](../plans/milestones/P03-authorized-retrieval.md#revised-end-to-end-flow).

Keep this foundation overview aligned with its linked behavior while preserving
historical measurements and frozen protocols. Record future capability changes
in their milestone flows rather than presenting them as original HW-01 behavior.
