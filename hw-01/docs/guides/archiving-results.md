# Archive and restore experiment evidence

This is an explicit copy-only Docker workflow. It does not run models, change
Git tracking, rewrite history, remove source bundles or reset the spending ledger.
Make is the host entrypoint; packaging, checksums, SDK calls and verification
execute in containers.

## Selection and local archive

`config/archives.yaml` defines named selections. `final-baselines` uses the
latest required matrix membership and the compact v2 evidence index. It checks
each covered observation against its original manifest, record and source
identities. Related preparation/evaluation bundles are selected by their
provenance references, rather than by age or directory-name heuristics.

From the repository root:

```sh
make hw01-archive-results ARGS='--selection final-baselines'
```

All selected source bundles must already exist under `results/submission/`.
The archive operation checks their original inventories and run-record reloads,
rejects symlinks/special files and potential credentials, and keeps every original
payload byte, including failed attempts, checkpoints and schema snapshots.
It embeds the complete selected membership snapshot and per-file checksums
inside a deterministic compressed archive. A full temporary restore must pass
before the cache and compact index are published.

The resulting paths, relative to `hw-01/`, are:

| Path | Purpose |
| --- | --- |
| `results/archives/<sha256>.tar.gz` | Ignored local compressed archive |
| `archive-index/<sha256>.json` | Compact index suitable for Git after review |
| `archive-index/<sha256>.remote.json` | Receipt after a verified S3 upload |
| `results/restored/<sha256>/submission/` | Isolated restored bundles, ignored |

The object key is `hw01/archives/sha256/<sha256>.tar.gz`. Repeating creation with
the same input bytes reuses the same archive/index. A different existing file
at a destination is refused. No creation timestamp is put into archive identity.

The limits are 512 MiB compressed/expanded payload, 64 MiB per file, 10,000
files and an 8 MiB internal manifest. This workflow targets small homework
evidence sets; larger archives require an explicit policy change.

## Verify and restore offline

Replace `<sha256>` with the checksum printed by archive creation:

```sh
make hw01-verify-archive ARGS='--index archive-index/<sha256>.json'
make hw01-restore-results ARGS='--index archive-index/<sha256>.json'
```

Verification checks the archive checksum/size, manifest identity, every payload
checksum, exact bundle inventories, covered membership and operational record
reload. Restoration first extracts into a private temporary directory, rejects
traversal, duplicate members, links and special files, and only then installs
the isolated directory. It refuses an existing restore destination and never
overlays live runs or the source submission directory.

Evaluate the restored v2 baselines using the existing scorer:

```sh
make hw01-evaluate-restored ARGS='--source-dir results/restored/<sha256>/submission matrix-native-v2-gold-20261024-72 matrix-native-v2-remaining-20261024-72'
make hw01-evaluate-restored ARGS='--source-dir results/restored/<sha256>/submission matrix-provider-v2-gold-20261024-72 matrix-provider-v2-remaining-20261024-72'
```

This uses the checkout's frozen corpus/gold/schema. Mismatched inputs or schema
remain errors. Restored records are not rewritten to fit the current profile.
Historical v1 source runs straddle the audited $4.50-to-$10 budget revision;
their combined evaluation additionally requires `--allow-budget-revision` and
the original ledger/policy backups. The archive deliberately does not export
private accounting files. Without those backups, individual v1 runs can still
be evaluated, but do not claim the same combined budget-normalized variant.

## Optional local Garage bucket

Generate first-use settings and start the pinned single-node service:

```sh
make hw01-archive-store-init
make hw01-archive-store-up
```

Initialization creates ignored `.env.archive` and
`results/garage-config/garage.toml` with unique random credentials and restrictive
permissions. It prints paths only and refuses to replace existing settings.
Garage initializes the single-node layout, key and `hw01-evidence` bucket from
those settings. No manual credential copy is necessary. Do not copy the example
placeholders into a running deployment.

The server runs as UID 10001, with read-only root filesystem and persistent
`garage-data` volume. Only the S3 port is exposed, on `127.0.0.1:3900` by default;
`HW01_GARAGE_PORT` can change the host port. RPC/admin ports are not published.
The archive client reaches `http://garage:3900` inside the Compose network.
`make hw01-archive-store-down` stops Garage and preserves its volume.

For an existing S3-compatible service, configure the `HW01_ARCHIVE_*` settings
from `.env.archive.example` instead; starting local Garage is optional.
Archive helpers never receive provider credentials. Offline archive/restore
helpers have networking disabled and do not load storage credentials.

## Upload and retrieve

```sh
make hw01-upload-archive ARGS='--index archive-index/<sha256>.json'
make hw01-download-archive ARGS='--index archive-index/<sha256>.json'
make hw01-verify-archive ARGS='--index archive-index/<sha256>.json'
```

Upload verifies the local archive first. If the object exists, the client reads
and verifies it instead of uploading over it. After a new upload, a full GET
must match the indexed size and SHA-256 before a receipt is published. Downloads
validate inner bundle integrity before publishing a local cache file. ETags and
remote checksum metadata are not treated as proof of the expected bytes.
Connection/read deadlines are bounded, and automatic SDK request retries are
disabled. A failed transfer never marks an archive as verified or overwrites a
conflicting local file. Retry with an explicit new command after inspection.

Garage does not provide S3 Object Lock or bucket versioning. Content-based keys
and conflict checks protect this client's normal operation, not concurrent
external writers or administrators. Every later download/restoration still
checks the expected checksum. See the official [compatibility reference](https://github.com/deuxfleurs-org/garage/blob/main-v2/doc/book/reference-manual/s3-compatibility.md)
and [single-node setup](https://github.com/deuxfleurs-org/garage/blob/v2.4.1/doc/book/quick-start/_index.md).

## Retention and publication

New bulk exports and detailed reports under `results/submission/` are ignored
by default. The repository's `.gitignore` explicitly allows only reviewed compact
snapshot files; future curated snapshots need a narrow reviewed allowlist.
`archive-index/` stays available for versioning. Existing tracked evidence remains
tracked: ignore rules neither remove it from Git nor rewrite its history.

An ignored output is not automatically archived. Run and verify archival before
any separately authorized cleanup; keep source copies until backup requirements
are satisfied. The twelve new v2 bulk bundles were checked against the verified
archive before adding the ignore rules. No source files were deleted or untracked.

Review and version compact indexes/receipts together with the relevant summaries.
An index without access to its archive is a provenance reference, not a portable
submission. A local Garage bucket is not reachable by reviewers; provide a
portable archive or an accessible retrieval location when handing off evidence.

The local cache, original exports and Garage volume can all live on the same
laptop. Back up archives or Garage data separately before deleting originals.
This workflow performs no deletion or untracking; any later cleanup is a
separately authorized action. Existing tracked evidence and new untracked raw
bundles stay in place throughout implementation and verification.
