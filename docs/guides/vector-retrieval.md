# Local embeddings and Qdrant — P03-E02

E02 uses a pinned CPU ONNX encoder in Docker and a dedicated local Qdrant
service. It does not use Ollama, a provider generator, LangChain or a hosted
embedding API. See the [execution report](../reports/P03-vector-retrieval.md).

The [execution profile](../../config/retrieval/P03-E02-profile-v1.json) freezes
model revision and file hashes, preprocessing, 384 dimensions, cosine similarity,
whole-input capacity and resource ceilings before encoding. NumPy/ONNX Runtime
are declared and locked through Docker `uv add`; no host packages are installed.

```sh
# Explicit download only: no text is sent to an embedding provider.
make prepare-encoder

# Network-disabled CPU encoding; publication refuses an existing output.
make encode-references

# Separate private network and new dedicated volume; no host ports.
make vector-store-up

# Saved vectors only. The frozen E02 manifest must match this encoding artifact.
make evaluate-vectors ARGS='evaluate --run-id e02v1 --output results/submission/P03-E02-v1/report.json'
make evaluate-vectors ARGS='lifecycle --run-id e02v1 --output results/submission/P03-E02-v1/lifecycle.json'

# Physical stop/start preserves the volume and does not re-encode anything.
make vector-store-stop
make vector-store-up
make evaluate-vectors ARGS='reload --run-id e02v1 --output results/submission/P03-E02-v1/reloaded.json'
make vector-store-stop
```

These are the original phase commands, not instructions to replace existing
results. Existing output/collection names fail before being overwritten. Restore
the saved evidence to reproduce this run; a fresh encoding changes its artifact
identity and needs a newly recorded experiment manifest. Its elapsed time is
also part of the saved encoding envelope. Final Garage archival belongs to S09.

`config/retrieval/P03-E02-v1.json` binds the saved encoding, profile, encoder,
store adapter, driver, lockfile, deployment and control sources. The Make entry
point supplies deployment/control files read-only; the live worker has no
provider credentials or extraction-ledger mount. Encoder model files remain
read-only during encoding. Model weights, vectors and database files stay ignored.

The encoder rejects inputs above 256 wordpieces rather than truncating rules.
It uses masked mean pooling and L2 normalization, one CPU thread, batch size one,
at most 104 unique inputs, no encoding retries and a 300-second encoding bound.
Repeated original questions share identical profile-bound vectors; authorization
is applied separately for every query. This is not a response cache.

Qdrant uses exact cosine search with mandatory scope, snapshot and eligibility
filters. For this tiny collection it returns the bounded eligible population
(at most 64 candidates), then the application applies the frozen score-tie rule
and takes three chunks. All returned IDs must match the trusted eligible set;
scores must agree with an independent cosine oracle within 2e-6. Source authority
is revalidated after search, before original source bytes become context. Database
payload text is never used as evidence. There is no hidden BM25 fallback.

Store calls have no automatic retries, a five-second request timeout and a
400-operation/900-second invocation ceiling. The profile also bounds total
planned phases. Qdrant has a 1 GiB memory ceiling; encoder/worker services have
2 GiB. Exact-search and lifecycle checks do not establish ANN performance,
production authentication, answer correctness or cloud cost savings.

The Qdrant service is left **stopped** after verification. Its dedicated volume
and the pinned model cache remain available. Do not delete or reset existing
extraction storage or cumulative spending to rerun this experiment.
