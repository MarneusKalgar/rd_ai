# P00-S08 — Low-risk legacy-name cleanup

Completed 2026-10-31 for the selected low-risk scope. No inference, settings
migration, persistent-resource rename, dependency update or Git publication ran.

| Surface | Outcome |
| --- | --- |
| `hw01-*` Make aliases | Removed alias rules, `.PHONY` entries and compatibility help. Canonical recipes and native/provider selection are unchanged. |
| Current instructions | Canonical commands in guides/reference/quality documents, README, AGENTS, report reproduction directions and archive environment-example comments. Repaired stale working-directory/build-context/bind-mount instructions and empty-directory wording. |
| Disposable names | Scratch prefixes `di-verify-`, `di-upload-`, `di-store-`; synthetic storage-test bucket `di-test`. |
| Environment/package contracts | `HW01_*` settings and package/lock metadata retained; coordinated migrations were not selected. |
| Runtime/storage | Compose project, named volumes, existing image names, real bucket/credentials and object keys retained. |
| Historical evidence | Archive format version identifiers, indexes, receipts, payloads, dated execution observations and historical application overview preserved. |

P00's original alias verification remains an accurate record of that migration.
This follow-up supersedes its compatibility policy for current use: call
`make check`, `make run`, `make reproduce-report`, etc. Removed aliases fail
instead of silently dispatching elsewhere.

Verification:

- Canonical help/check/native/provider dry runs resolve correctly, without model
  requests or added provider permissions.
- `make -n hw01-check` fails with exit 2, as intended.
- Docker Ruff lint/format passed; **39 archive/storage tests passed** in 67.87s.
- Current documentation links resolve; every preexisting archive-index JSON
  checksum, including receipts and proof records, matches its pre-cleanup value.
- The full 938-test P00 gate remains a separate prior measurement; it was not
  redundantly rerun for aliases, documentation and disposable labels.

The selected low-risk work and risk dispositions are concluded. Higher-risk
migrations remain deferred pending a concrete need, scope and the
[S08 preservation gates](../plans/milestones/P00-project-consolidation.md#p00-s08--legacy-name-cleanup-and-risk-gated-migration-review).
No namespace-wide removal or additional model/security coverage is claimed.

A subsequent explicit request selected the remaining runtime/package/project
work. See the [runtime migration record](runtime-name-migration.md); the
low-risk observations above describe the earlier slice unchanged.
