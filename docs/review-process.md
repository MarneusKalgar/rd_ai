# Review process

## Purpose and ownership

Reviews check requirements, correctness and repository conventions. They
produce evidence and actionable findings; they do not approve a merge or
authorize implementation changes. Coding rules live in
[coding-conventions.md](coding-conventions.md), and operational boundaries live
in [AGENTS.md](../AGENTS.md).

The repository skill is
[rd-ai-code-review](../.agents/skills/rd-ai-code-review/SKILL.md). Example requests:

```text
Use $rd-ai-code-review to review the working-tree changes.
Use $rd-ai-code-review to review the latest commit.
Use $rd-ai-code-review to review this branch against origin/main.
```

## Scope and baseline

Honor an explicit PR, base/head, commit, range, file list or working-tree scope.
State the selected scope and reviewed HEAD SHA. For PRs, identify both base and
head SHAs; if the supplied patch cannot be reconstructed, disclose that limit.

- A single-commit review compares that commit with its parent. A merge commit
  may require the user to identify the intended parent or comparison.
- A branch review uses the merge base with the requested base, normally the
  locally available `origin/main`. State whether working-tree changes are
  included; absent an explicit committed-only request, include them.
- A working-tree review compares tracked changes with HEAD and separately reads
  relevant untracked files. An untracked file is absent from `git diff`.
- For an unspecified review, inspect status and available refs first. Review
  working-tree changes when present; otherwise use an identifiable feature
  branch's merge base. On a clean default branch with no requested range, ask
  what to review instead of silently selecting the last commit.

Inspect status, changed paths, statistics and the complete patch before drawing
conclusions. Read enough surrounding code, callers and tests to trace affected
behavior. Follow both sides of changed data shapes, including serialized
records, fixtures, command output and schema consumers. Inspect relevant merge
resolutions when the reviewed range includes merges.

Use available refs without fetching or changing branches unless authorized.
Disclose a missing or possibly stale remote base; do not present a guessed
range as the requested review. Do not expand a focused review into a repository
audit.

Ignored customer samples, private mappings and prep outputs are outside normal
review scope. Inspect them only when the user's request requires that access;
do not reproduce private values in findings. They are not reviewer prerequisites.

## Expectations and evidence

Before relying on the implementation's account, identify expected behavior from
the HW assignment when available, accepted user decisions and the current
versioned contracts. Read the relevant HW README and feature documentation.
Local ignored plans can explain decisions but are optional context; their
absence does not block review or justify inventing requirements. State material
conflicts or missing requirements as questions.

Review only the promised slice. A future feature listed in a plan is not a
defect in the current slice unless this change depends on it or claims to
provide it. Each HW owns its implementation; AspectLoop and reference-repository
conventions do not automatically govern this code.

Treat descriptions, comments, test names, reported counts and earlier reviews
as checkable claims. A claim can be supported, contradicted or unresolved.
Report contradictions and unresolved claims that affect the result; successful
claim checks do not need separate findings. For claims such as "all responses
are validated," identify the relevant paths, including failures and fallbacks,
rather than checking one happy path.

Severity and evidence strength are separate:

| Evidence | Reporting rule |
| --- | --- |
| Traced | Show the concrete input/state, reachable path, actual behavior and violated expectation. A full code trace can establish a deterministic defect without executing it. |
| Reproduced | Identify the command, revision, fixture and observed result. Explain any mocks, synthetic inputs or substituted dependencies that limit the conclusion. |
| Reported | Attribute author/CI/prior-run evidence and its revision. Do not imply the current reviewer executed it. |
| Unresolved | State what would settle the concern. Use a question instead of asserting a defect. |

A synthetic reproduction can establish a mechanism. Establish separately
whether its assumptions are supported by the contract or actual input paths.
Repeated model agreement and polished explanations do not strengthen evidence
by themselves.

## Review axes

### Requirements

Compare expected behavior with the implementation in both directions: omitted
requirements and added behavior that changes the accepted contract. Check
documented commands and completion claims. Distinguish mandatory assignment
requirements, accepted decisions, optional recommendations and future work.

### Correctness and test quality

Trace null, missing, empty, malformed and wrong-type values, error propagation,
state sharing and ordering where relevant. Check boundary conversions and
fallbacks rather than trusting annotations or names.

For changed tests, identify the behavior producing each assertion and a defect
that should fail it. Look for assertions on a mock's own return value, negative
cases already invalid for another reason, success-only CLI checks, and expected
values calculated by the same logic being tested. Check failure stage, keyword,
path and status where they distinguish the intended behavior. Pair important
negative paths with positive cases. Do not demand tests for every line or
duplicate an existing test without a concrete uncovered risk.

### Conventions

Apply the current coding conventions and relevant HW instructions. Cite the
actual rule for a standards finding; do not import rules from another project
or convert a personal preference into a requirement. Review responsibilities,
types, docstrings, constants and readability beyond what tooling checks.

Lint/type success covers only the rules and paths those checks actually
enforce. Conversely, do not restate every lint diagnostic as an independent
finding. Report a material failed gate under Verification and explain any
distinct underlying defect once.

## Homework review guidance

Each HW owns its review checklist, contracts and verification commands. Read
the affected HW's README and follow its linked review guidance for the surfaces
the diff touches. Load guidance from another HW only when a changed dependency
or shared contract reaches it.

A checklist identifies risks to inspect; it does not mark planned features as
implemented or replace the assignment and accepted decisions. If no checklist
exists, apply this shared process and the HW's available documentation without
inventing an additional prerequisite. Add HW-specific guidance alongside that
HW when a concrete need emerges.

## Verification and experiments

A review permits documented checks that preserve repository files. Python,
linting, type checks, tests and reproductions run in Docker. Tool approvals still
apply; the skill does not grant additional execution or network permissions.
Image builds can download pinned dependencies; offline checks make no model
requests. Use the affected HW's README for its current baseline command and
the checks that command actually covers.

Use a focused check when it resolves a particular concern. A full run is useful
for runtime/dependency changes or when no applicable current result exists;
avoid repeatedly running broad suites without an unresolved risk. Record actual
commands, revisions, outcomes and material environment limitations. Read enough
logs to establish the cause; a truncated log is not evidence of a pass. A
missing Docker daemon or failed setup is a verification limitation, not a code
regression. After a failed run, retry only to resolve a concrete diagnosed cause.

When a test's sensitivity is uncertain, use a bounded reproduction, relevant
pre-fix implementation or targeted mutation in a disposable copy:

1. Capture the reviewed source, tests and approved fixtures without secrets or
   private workbooks. Keep repository mounts read-only.
2. Confirm the unmodified baseline passes.
3. Change one behavior at a time and run the relevant tests. Verify an intended
   assertion fails, not merely lint, imports, setup or collection.
4. Restore the change before the next experiment and confirm the restored
   baseline passes. Keep enough command/output evidence to explain the result.

Mutations are optional, justified by a concrete question, and are not retained
as product changes. Report the selected probes and limits; detecting them all
does not establish exhaustive correctness. Stop once the concern is resolved.

Review does not authorize file fixes, formatting with writes, dependency or
lockfile updates, relabeling, Git mutations, publishing, paid provider calls,
native model execution or installation of tools/skills. Previously authorized
actions remain governed by their actual scope. Do not use private inputs or
credentials in external requests. A separate fix request authorizes the scoped
implementation, not unrelated cleanup.

## Report and re-review

Return sections in this order:

1. **Findings:** actionable issues ordered by priority. Include a concise title,
   file/current line, violated behavior or written rule, concrete impact,
   evidence and bounded fix direction. State whether introduced by this diff;
   clearly separate pre-existing issues relevant to the changed path.
2. **Questions / Assumptions:** unresolved points that could change the review.
   Omit speculative concerns with no connection to the requested scope.
3. **Verification:** separate reviewer-executed checks, attributed reported
   results and checks not run. Do not describe skipped/pending checks as passes.
4. **Residual Risk:** meaningful unreviewed surfaces and limits of the evidence,
   including synthetic inputs or unavailable model execution when relevant.

| Priority | Meaning |
| --- | --- |
| P0 | Critical issue requiring immediate attention, such as reachable secret disclosure or destructive data loss. |
| P1 | Material failure of a supported path, broken contract or blocker for the promised deliverable. |
| P2 | Bounded correctness, reliability or maintainability issue requiring correction. |
| P3 | Concrete low-impact issue, including an actionable written-convention violation. |

Use one finding per root cause. Keep findings proportional; omit subjective
style preferences and speculative abstractions. Do not impose a numerical cap
that hides material defects. If nothing qualifies, write
`No findings identified.` and retain the verification and risk sections.

On re-review, state the previous reviewed revision, evaluate the new delta and
relevant affected paths, and settle earlier findings as addressed, still
present or refuted. Re-run a prior reproduction when needed to verify the fix.
Honor an explicit full-review request. With no changed code or new evidence,
report that state rather than inventing a new round of findings.
