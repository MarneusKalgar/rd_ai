# P03-S09 preservation and recovery

All processing runs in Docker. These commands make no model, embedding,
subscription-judge or paid-provider calls. Start from the project root.
Existing evidence is never overwritten; use the archived snapshot for recovery.
The first command block records the original preparation/recovery phases; do
not repeat snapshot/store creation against existing results. For repeat recovery,
use the published archive index and the download/restore/verify commands below.

The original Qdrant is read-only to the export operation. Recovery writes only
to `qdrant-s09-restored`, a separate service and volume with the same pinned image.
Exact partially restored collections may be checked and reused; changed/extra
collections fail closed. No automatic deletion or replacement occurs.

```sh
make check
make closeout-check
docker compose --env-file .env.compose -f compose.yaml -f compose.s09.yaml up -d qdrant-e02 qdrant-s09-restored
make closeout-export
make closeout-restore
docker compose --env-file .env.compose -f compose.yaml -f compose.s09.yaml stop qdrant-s09-restored
docker compose --env-file .env.compose -f compose.yaml -f compose.s09.yaml up -d qdrant-s09-restored
make closeout-reload
make closeout-snapshot
make closeout-verify
make closeout-seal
```

Snapshot freezes public application source, tests, configuration, docs, approved
inputs/gold/reference texts, the five P03 evidence directories and controllers.
Private workbooks, `.env` files, the spending ledger and host subscription
credentials are excluded. The whole repository is not copied. Encoder files
are SHA-256 verified, then encoded as bounded base64 parts to fit the existing
text-only, 64-MiB-per-file archival policy. Recovery decodes and checks their
original frozen hashes; it does not execute the encoder or download weights.

Seven explicitly reviewed source files contain synthetic authentication fixtures
or header-construction templates that match the archive's credential-pattern
scanner. The snapshot stores those copied files in base64 with original hashes;
the decoder restores their exact bytes in a temporary tree. The original
checkout is unchanged. Unknown flagged files are not automatically exempted,
and the existing archive scanner is not weakened. The same exact-path codec
preserves 30 `__init__.py`/`__main__.py` files under canonical encoded filenames,
because the archive policy disallows leading underscores. Original names are
restored only in the temporary source tree. Encoding is not encryption.

The logical Qdrant export retains all vectors/IDs/payloads from the E02 report's
collections. Reload checks all forty query outcomes and the independent cosine
oracle, including eligibility filters and source revalidation. The isolated
store also exercises scope, currentness, revocation, update and deletion.
Logical export/reload is not a Qdrant binary snapshot or a portability claim
across arbitrary future server versions. E02's original dependency files are
preserved separately from the later optional integration environment.

`verify` reconstructs lexical results, I01 contexts/captures, E03 physical
responses, all saved judge grades, human overall labels and improvement metrics,
then replays actual answers through direct/LangChain paths. It requires no
network or ledger. The historical ledger reconciliation remains documented in
S08; private reservations are not exported or fabricated.

After sealing, the selected evidence index is generated from the verified bundle
inventory and stored under `archive-index/selections/P03-closeout.json`.
Use the existing Garage workflow:

```sh
make archive-results ARGS='--config config/archives-P03.yaml --selection P03-closeout'
make archive-store-up
make upload-archive ARGS='--index archive-index/<sha256>.json'
make download-archive ARGS='--index archive-index/<sha256>.json'
make restore-results ARGS='--index archive-index/<sha256>.json'
make closeout-verify ARGS='--bundle /workspace/results/restored/<sha256>/submission/P03-S09-v1'
```

Full GET and checksums establish byte identity; the isolated restore/reconstruction
establishes usable recovery. Download does not require deletion of the local
cache. Original source evidence and all existing storage volumes are retained.
Garage and the cache are on the same laptop, not off-device backups.

LangChain remains in the optional integration image/group only. It is absent
from the default runtime, retained solely to reproduce the rejected I01 trial.
Deleting its historical lock/profile would invalidate the frozen evidence.
