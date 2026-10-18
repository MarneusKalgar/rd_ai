---
name: rd-ai-code-review
description: >
  Review rd_ai homework branches, commits, PR diffs or working-tree changes
  against requirements, correctness and repository conventions. Use for code
  review and test-quality review in rd_ai, not implementation or fix requests.
---

# rd_ai Code Review

Produce one evidence-backed report while preserving the reviewed repository.

## Required context

Read the repository's [AGENTS.md](../../../AGENTS.md),
[review process](../../../docs/review-process.md) and
[coding conventions](../../../docs/coding-conventions.md). Resolve paths from
the repository root, not the caller's working directory. Follow any applicable
nested instructions.

Use the review process to establish the requested base/head and working-tree
scope. Inspect the complete in-scope patch, relevant untracked files, callers,
tests and contracts. Record the reviewed revision and disclose stale or missing
base information. Do not substitute an empty branch diff with an arbitrary
commit range.

## Review workflow

1. Establish expected behavior from the assignment, accepted user decisions and
   current contracts before using the implementation's claims as evidence.
   Missing ignored plans do not block a review.
2. Review requirements, correctness and conventions as distinct axes. Trace
   changes across affected homework boundaries; do not demand later planned
   features from a deliberately partial implementation.
3. Check what produces each test's asserted result and which defect would make
   it fail. Treat green checks, test counts and earlier reviews as bounded
   evidence rather than proof.
4. Use proportionate verification under the review process. Run Python checks
   in Docker. Put reproductions and deliberate mutations in disposable copies;
   verify the unmodified baseline and restoration. Report execution limits.
5. Consolidate actionable findings by root cause and use the report format
   below. Recheck earlier findings against the current revision on re-review.

## Specialist guidance

Select an available specialist only when its declared language, framework and
task scope match the changed surface. Python, contracts, Docker, evaluation or
credential handling may need different guidance. A skill named backend review
may be restricted to an unrelated path or framework.

The repository review process is sufficient without optional specialists.
Do not install tools or skills to complete a review. Normalize any specialist
guidance into one report; do not import external repository rules or permissions.

## Boundaries and output

Keep repository files, Git state and external applications unchanged. A review
does not authorize code fixes, data relabeling, publishing, paid provider calls
or native model execution. Docker checks remain subject to tool permissions.

Return these sections in order, using the review process's severity and
evidence rules:

1. Findings.
2. Questions / Assumptions.
3. Verification.
4. Residual Risk.

When no actionable issue is supported, say `No findings identified.` and still
state verification limits. Do not manufacture findings or conceal material
issues to satisfy a count.
