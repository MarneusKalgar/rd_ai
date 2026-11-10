# Optional LangChain integration trial — P03-I01

I01 compares the direct application path with pinned LangChain/Qdrant integration.
It uses saved E02 vectors and synthetic capture responses, not new encoding or
generation. The [report](../reports/P03-langchain-integration.md) records parity,
overhead and the decision to retain direct integration.

The optional `integration` dependency group was added with Docker `uv add`.
It is installed only in the `integration` Docker target. Default runtime/check
images do not install LangChain or the Qdrant SDK. The optional group remains
locked for reproducing this trial; it is not permanent application adoption.

```sh
# SDK-specific tests; no model or database needed.
make integration-check

# Original real-store trial; an existing output is never overwritten.
make vector-store-up
make integration-trial ARGS='--output results/submission/P03-I01-v1/report.json'
make vector-store-stop

# Network-disabled semantic reproduction from saved vectors and report.
make integration-reproduce ARGS='--report results/submission/P03-I01-v1/report.json --sha256 f8388bdaae0a40cf045f0d69ff9dee67a7e20fb215864e37a56e534347d47604'
```

These are original phase commands, not permission to replace evidence or rerun
the completed trial repeatedly. The live phase uses the existing E02 collections
and creates one separate control collection. Preserve their names/history. The
reproduction phase neither starts Qdrant nor loads a model; it reconstructs
contexts and canonical request/validation records, not the original timing or
live HTTP events. Obtain the report checksum from the compact versioned summary.

The current optional-group lock differs from E02's original lock. Its byte-exact
`uv.lock` and `pyproject.toml` are preserved under
`config/retrieval/I01-inherited-runtime/`. I01 explicitly verifies these originals
alongside E02 source/vector bindings and separately binds its extended runtime.
E02's manifest and loader were not weakened or rewritten. Running E02 itself
against its strict historical bindings still requires its original source/runtime;
do not edit its checksums to make the current dependency declaration pass.

The live worker uses a private network with no provider credentials, model mount
or extraction-ledger mount. Its inherited evidence is read-only; only the new
I01 output folder is writable. Tracing flags are false, tracing credentials are
rejected, and no LangSmith account/export is configured. LangSmith's Python
package is a transitive optional dependency, not a tracing deployment.

`LangChainQueries` borrows its client. It uses the explicit by-vector API with
no embedding object, no cloud inference, exact search and mandatory flat-payload
filters. The pinned wrapper additionally fetches collection metadata per query.
Returned `Document` payload strings and authority-like metadata are ignored;
only validated locators/scores reach application-owned source reconstruction.

Capture-only requests use a separate fixture answer schema and provisional test
settings. They are not a frozen E03 generator profile or proof of live model
admission/accounting. The direct path and LangChain runnable sequence call the
same application functions. Independent tests check expected request shape,
skips, raw-response preservation, validation failures, forged citations and
source authority. No automatic query rewrite, repair, fallback or framework
retry is added. Actual S07 response replay remains an S08 follow-up.
