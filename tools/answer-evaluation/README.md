# S08 review preparation

This contains S08 preparation, deterministic reporting, actual-response replay
and the provisional subscription judge runner. Human calibration remains open.
Human review is optional complementary evidence for R&D improvement reporting.
`make answer-evaluation-publish` reconstructs whole-population and frozen
answerable/negative-control rubric-pass yields and percentage-point deltas.
Unknowns, skips and errors earn no judge pass; negative-control yield is not
a safety-success rate. Human-calibrated reliability remains a separate claim.
It verifies S07 source bindings and the three immutable journal hashes, retains
all 120 outcomes and revalidates parsed answers/citation eligibility. The separate
report command reconciles the API ledger through a read-only mount. These checks
do not establish semantic correctness.

```sh
make answer-evaluation-prepare
make answer-evaluation-check
make answer-evaluation-report
make answer-evaluation-replay
make answer-review-shuffle
make answer-human-overall-review
```

Preparation has no network, provider credentials, ledger mount or model calls.
New operational code stays outside the hash-bound application `src/` inventory.
Existing packet files may be reproduced only if bytes agree; human edits cannot
be overwritten silently.

Review files are under ignored `results/submission/P03-S08-v1/`:

- `human-feedback-20261112.json`: explicit overall labels and the user's grouped
  reasons; preserves the earlier feedback and specific-label precedence.
- `human-item-labels-20261112.json` and `human-labelled-review-20261112.md`:
  consolidated labels and annotated bundles for all 36 sampled items. Overall
  labels do not populate the granular `human-review.json` schema or establish
  judge admission. No-answer rejection and abstention appropriateness differ.
- The `20261112-R01` feedback, consolidated-label and annotated-packet files
  supersede the original overall label for `3a8ed26ec1fecf9e`, restored to pass
  by the user. Current totals are 18 pass, six partial and twelve no-answer/not-pass;
  original files remain preserved.
- `human-overall-review.json`: completed overall review of the exact 36-item
  sample, source hashes and descriptive human/judge comparison. Reproduce with
  `make answer-human-overall-review`. Unknown and ungraded judgments stay separate;
  this does not manufacture granular anchors or admit the judge. The report
  command revalidates this artifact against its sources before publication.
- `calibration-review.md`: eight questions, all three arms (24 jobs).
- `audit-review.md`: four separate questions, all three arms (12 jobs).
- `review-template.json`: blank decisions. Copy to `human-review.json`, add your
  reviewer identity and complete decisions with evidence/rationale. Leave unknown
  decisions explicitly unknown rather than guessing. For import, set authority
  to `human-reviewed`, add `reviewed_without_judge_grades: true`, and use
  `pass`/`fail`/`unknown` for verdicts. `claim_support` is an ordered list of those
  decisions, one per explicit claim (empty for a non-answer). Include evidence
  and rationale; unknown decisions remain unknown. `make answer-human-review`
  validates identities, phases, duplicates and coverage, then compares calibration
  and audit labels separately. It never rewrites the original rubric or turns
  general endorsements into anchors. Do not consult judge verdicts to create
  supposedly independent human anchors.
- `profile.json`: sample membership and source receipt identities; this is a
  preparation profile, not the complete frozen judge-execution profile.
- `bundles.json`: all 120 opaque-ID evaluation bundles.
- `private-mapping.json`: evaluator-only mapping; never supply this to the judge.
- `human-feedback-20261111.json`: the user's general endorsement of six
  calibration and four audit items, preserved separately from granular rubric
  decisions. Unmentioned items remain unreviewed. This feedback alone does not
  approve expected propositions or establish judge calibration. Audit feedback
  must not enter calibration examples or the judge prompt.

The v1 packets use the original fixed no-context/BM25/vector ordering within
each question. Opaque IDs therefore do not fully blind arm identity. Preserve
the existing packet and feedback; a later review presentation should use a
separately versioned, reproducibly shuffled order and retain the same item IDs.
Report this exposure when interpreting the initial human feedback.
The separate `calibration-review-v2.md` and `audit-review-v2.md` files implement
the declared hash-based shuffled order; their manifest is `review-order-v2.json`.

Expected propositions are agent-authored technical expectations, requiring human
verification against the sources; they are not new human-approved labels. Read
the actual cited passages and report missing evidence, contradictions and false
additions. Keep full-answer correctness, completeness and claim grounding
separate. No-context answers have no grounding credit. Application skips and
provider failures are not model abstentions. Do not treat a blank review as a
pass. Calibration and audit outcomes stay separate; audit labels never enter
the judge prompt.

The host Codex CLI upgrade to 0.167.1 resolved the observed version-command kill;
ChatGPT authentication is confirmed. Actual S07 response replay passed on all
120 jobs: direct and LangChain paths preserve 108 replies, including the upstream
error, and 12 skips. It uses actual S07 requests/schema/raw replies, rather than
I01's incompatible synthetic fixture schema. This is parity evidence, not new
model observations or an accuracy gain. Only the optional integration image
contains LangChain; no database, encoding or model call runs in replay. Small
composition timings are not a controlled throughput benchmark.

## Provisional subscription judging

`config/evaluation/P03-S08-judge-v1.json` selects Sol/medium, CLI 0.167.1 and one
CLI attempt per job: two synthetic controls followed by 107 saved valid answers.
The other 13 original jobs remain explicit skips/failure and are never sent for
model grading. Human anchors remain incomplete; neither synthetic controls nor
the user's general endorsements calibrate the judge. No semantic adoption pass
can follow from these AI grades.

Execution completed: 109 valid provisional records in distinct sessions, including
107 answer grades and two controls. Do not rerun the original or continuation
invocations. Model-free summary/publication commands reconstruct saved records.
See [the evaluation report](../../docs/reports/P03-evaluation.md) for paired
counts, usage and observed correctness-versus-grounding ambiguity. Human
calibration and audit remain unresolved.

Docker freezes requests and controller/prompt/schema bindings. The host shell
only orchestrates Codex commands, redirects records and enforces a 180-second
attempt watchdog and 7,200-second phase deadline. Each attempt starts from a
fresh temporary directory, disables user config, project instructions, host
skill discovery and listed tool/app/plugin/browser capabilities. Calls use
ChatGPT sign-in; API-key environment variables are excluded. Per-job metadata
must show Plus ordinary access, zero purchased credits, fresh quota data and
less than 90% used in both quota windows. Stop on unknown state; never purchase
or reset credits, switch models or use an API fallback. CLI internal transport
behavior is opaque: one CLI invocation is not proof of exactly one physical
provider request. The 12,000 output-token bound is an observed post-call guard,
not a provider-enforced generation ceiling.

Retain raw events/verdicts/errors. Validation checks schema/identity, proposition
and explicit-claim coverage, exact cited quotations, consistency, usage and
absence of tool calls. Those mechanical checks cannot establish entailment,
whether the judge found every summary assertion, or model reliability. Actual
hosted weights and reported model identity may be unavailable; record missing
metadata explicitly. Subscription usage is separate from API charges; no
zero-cost API reservations are fabricated.

The original phase stopped after its first positive control because Codex emits
the known `skip_host_skill_discovery` startup warning as an error item. The first
grade and original strict rejection remain intact. R01 binds a separate parser
and derived launcher recognizing only that exact pre-turn client notice. Other
errors, repeated/late notices and all tool events still fail. R01 reuses the first
response without inference and admits only unsent jobs. An existing failed
attempt cannot be retried automatically.

```sh
make answer-judge-freeze             # already frozen; identical reproduction only
make answer-judge-run                # original stopped phase; do not repeat
make answer-judge-r01-freeze          # binds the separate recovery controller
make answer-judge-r01-run             # single bounded continuation, no retry loop
make answer-judge-r01-summary         # model-free reconstruction, retains failures
make answer-evaluation-report         # paired counts; AI grades stay provisional
```

The complete 120-job report retains ungraded/failed outcomes and exposes human
coverage separately. Judge manifests, raw records and provisional summaries stay
ignored and need archival at S09. The API ledger is mounted only for offline
reporting and remains read-only. Never invoke an ad hoc judge from the repository
or reuse this chat as a judge session.
