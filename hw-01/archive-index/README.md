# Archive indexes

The archive command writes `<sha256>.json` here after a full temporary restore
has verified the archive. These compact files identify the content-addressed
archive, its selected bundles and membership checksum. Per-file payload hashes
live inside the archive. Successful uploads add a separate small
`<sha256>.remote.json` download-verification receipt, without credentials.
The documented implementation acceptance also records a compact
`<sha256>.verification.json` with restored-evaluation and source-integrity results.
Use `<sha256>.json` as the CLI index, rather than either receipt/report file.

Review indexes and receipts before explicitly adding them to Git. The compressed
cache stays ignored under `results/archives/`; isolated restores stay ignored
under `results/restored/`. Source exports, Git tracking and history are untouched.

Use the [archival guide](../docs/guides/archiving-results.md) for configuration,
Garage setup, verification, retrieval, offline evaluation and backup boundaries.
