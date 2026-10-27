# Section 9: reproducibility and verification

Verified 27 October 2026. Section 8 was committed as `d1858a0`; this verification
uses that tracked source plus the explicit section 9 candidate changes. It
validates the current research baseline and saved comparison, not unattended
production readiness or performance on unseen documents. No new inference ran.

## Gates and evidence

| Gate | Verified outcome |
| --- | --- |
| Portable saved-result verification | `make hw01-reproduce-report` passed from an isolated source export with no private environment files, spending ledger or preexisting restore. The only supplied runtime artifact was the indexed public archive. Docker/Compose and Make suffice; no host Python, model runtime or provider key was used. |
| Source isolation | Exported 424 tracked files plus five explicitly listed new candidate files, preserving the relative guidance symlink. Original workbooks, private preparation, Git internals, credentials and ignored results were excluded. Credential-pattern matches were limited to reviewed intentional test strings and detector/interpolation code; the archive scanner was not weakened. This is a bounded format scan and source-boundary check, not proof against every possible secret or identifier. |
| Frozen data and contract | The complete gate validated the frozen corpus/input/schema/gold hash chain, all thirty neutral inputs and ten approved gold objects. No source, label, approval record or authoritative PO schema changed. Historical human approval is retained; this work adds no new human factual review. |
| Extraction implementation | The full suite passed for adapters, injected transport/lifecycle, JSON/schema validation, bounded retry/correction, admission, failure retention, deadlines, dependency stops and accounting. Loopback services are deterministic fixtures; no external model was called. |
| Historical experiments | Exact membership remains 240 attempted observations, eight thirty-input variants, with ten gold cases per variant. Original failed/truncated outcomes and reused observations remain visible. Screening, optional models and assisted workflows stay separate. |
| Report | Restored evaluation exactly matched the published full evaluation. Quality/operations/usage and fifteen per-field report rows matched; summary token/time populations were independently checked against saved attempts. The real CLI rejected a copy changing Flash v2 baseline accuracy from 100.00% to 99.00%, exiting 2. |
| Implementation checks | **938 tests passed in 308.19 seconds**, Ruff lint/format, strict mypy over **206 source files**, frozen gold validation and offline preflight, all from the isolated export. |

## Closing the private-ledger dependency

The new [public evaluation policy](../../config/evaluation-budget-policy.json)
retains the historical $4.50→$10 revision metadata and binds its use to thirteen
exact original manifest hashes. It permits read-only aggregation across that
administrative cap change. It is not a spending ledger, a provider billing
statement or authority for new calls. Model/runtime/context/sampling/deadline/
retry controls remain in variant identities; overlapping inputs remain errors.

`evaluate --budget-policy <file>` is mutually exclusive with the original
`--allow-budget-revision` local-ledger audit. Tests exercise the real CLI after
deleting both the fixture ledger and revision backup: metrics match the original
ledger-audited evaluation, no HTTP requests are added, and no ledger is recreated.
Changed/unlisted manifest bindings and malformed revision chains are rejected.
Additional tests deliberately change quality, latency, cost, usage and per-field
claims and verify that the report checker detects each defect.

The `reproduce` service has no network, provider environment file, model
dependencies or named results volume. It mounts the archive, index and report
read-only and writes only isolated restores/reproduction receipts. It calls
versioned application code and the shared scorer, never archived Python drivers.
Original records, unknown-charge holds and live spending policy are unchanged.

## Reproduce

Follow [the reproduction guide](../guides/reproducing-results.md) to provide the
indexed public archive, then run from the repository root:

```sh
make hw01-reproduce-report
make hw01-check
```

The first command verifies cache bytes/manifest, isolated payloads and exact
bundle inventories before scoring; an existing restore is checked rather than
trusted. It reproduces **84 bundles / 1,594 payload files**, **240 observations /
eight variants**, and the report tables. Its receipt includes the public policy
hash `467653a2f13db56a68fe559856cfcbde96a6ef4044bdbacd762eadad693c4efc`.
Raw logs and the clean-export inventory belong in ignored archived evidence;
compact selection/index/receipt files and this report remain reviewable in Git.

The section 9 proof archive contains **15 bundles / 542 payload files**
(3,560,649 compressed bytes), with full Garage GET verification and exact
source/restored payload equality:

- [Archive index](../../archive-index/4dddebd29d310e883c5e5a3fb0f026b187ba4c80b9b7c279567d33ecec950dd1.json).
- [Garage receipt](../../archive-index/4dddebd29d310e883c5e5a3fb0f026b187ba4c80b9b7c279567d33ecec950dd1.remote.json).
- [Restore verification](../../archive-index/4dddebd29d310e883c5e5a3fb0f026b187ba4c80b9b7c279567d33ecec950dd1.verification.json).
- [Explicit selection](../../archive-index/selections/section9-verification.json).

Selection `section9-verification` retains the new proof plus matrix source runs
and the consolidated evaluation. The one-command reproduction still consumes
the separately pinned section 8 archive identified in its public policy; these
proof records do not silently substitute another archive identity.

## Limits and current disposition

The isolated export excludes this machine's ignored inputs and settings, but
the checks reused the existing Docker engine, image/dependency cache and host.
This is not a newly provisioned machine or uncached network-install test. A
recipient must obtain the separately stored public archive; local Garage is not
public anonymous hosting. Garage and repository on one laptop are not off-device
backup. Future availability and pricing of model routes were not rechecked.

The historical requirement to run everything, including local inference, through
Docker has been superseded by the accepted native-Ollama choice on this Mac.
Offline verification remains Docker-only. New local inference requires explicit
native runtime/model setup; Docker Ollama was not restarted or downloaded.
New paid runs still require their separately approved command and allowance.

Sections 8–9 can be considered complete for the recorded analysis/reproducibility
scope. This is not a homework finish criterion. The development-gold leakage,
unlabeled twenty, unresolved historical billing holds and single-machine backup
limitations remain disclosed. Deferred 7.3 experiments and independent reviewed
evaluation remain separate decisions, not automatically scheduled work.
