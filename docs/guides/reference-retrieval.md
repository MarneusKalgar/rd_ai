# Offline authorized reference retrieval — P03-E01

E01 is implemented without embeddings, a database, model calls or ledger access.
Use the [P03 plan](../plans/milestones/P03-authorized-retrieval.md) for the later
Qdrant, generation and LangChain work. The [E01 report](../reports/P03-reference-retrieval.md)
records the controlled fixture results and their limits.

Run from the repository root; Make uses network-disabled Docker:

```sh
make validate-retrieval-protocol
make build-reference-index ARGS='--output results/submission/P03-E01-v3/index.json'
make evaluate-retrieval ARGS='--output results/submission/P03-E01-v3/report.json'
make evaluate-retrieval ARGS='--check-result results/submission/P03-E01-v3/report.json'
```

Publication refuses existing output paths. To reproduce an existing report, use
`--check-result`, not a replacement output. Only measured elapsed times are
excluded from deterministic equality. Build/evaluation stdout contains complete
JSON evidence; redirect it when needed. Do not commit bulky results.

The frozen protocol is `config/retrieval/P03-E01-v3.json`. It binds public source
texts, catalogs, evaluator-only query fixtures, source implementation, PO schema,
contract reference and a separate plan snapshot. V1 and v2 are superseded
development protocol identities, not accepted evidence; they intentionally fail
against changed implementation bytes. No queries, relevance labels or adoption
threshold were tuned after observing rankings. A future change requires a new
protocol identity and an explicit comparison, not rewriting these bindings.

`build_snapshot` constructs whole-rule chunks. `retrieve` accepts a trusted
fixture scope A/B, effective time, snapshot and explicit exact/BM25 method. It
never reads query relevance labels. The CLI evaluates frozen fixtures, rather
than exposing an authenticated public endpoint; selecting a fixture principal
does not authenticate a user. Saved snapshots can be JSON-reloaded using the
strict `Snapshot` model; retrieval revalidates them against their selected
catalog and original bytes. Historical replay requires an explicitly selected
historical catalog and is not a way to use a stale handle on a current catalog.

Source IDs, versions, hashes and UTF-8 half-open byte spans accompany exact
quotes. `validate_evidence` rejects modified citations and ranking against the
same request and current authority. Structural conflict keys are trusted catalog
metadata; this is not semantic contradiction detection over arbitrary prose.

Query text cannot widen eligibility or authorize fetching links. Missing/invalid
scope, source changes, stale/mixed snapshots, symlinks, escaping paths and
resource overruns fail closed. No source content is silently cropped. There is
no response cache, external tracing, query rewriting, fallback or source repair.

For a new catalog/source snapshot, preserve the old one, update source and
derivation bindings and explicitly version the protocol. Keep gold, predictions,
diagnostic verdicts, private sources and expected-answer fixtures outside the
retrieval collection. Technical relevance fixtures are not human-reviewed PO
gold or evidence of unseen-data performance.
