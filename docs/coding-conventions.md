# Coding conventions

These conventions apply to humans and agents working in this repository.
Each homework owns its tooling configuration; shared conventions live here
so agent instruction files do not maintain separate copies.

## Readability and layout

Readability takes priority over saving lines. Code should be easy to follow
step by step, including for someone learning Python.

- Separate logical blocks with a blank line: setup, guards, processing,
  construction of a result, and return/output. Keep closely related statements
  together; do not put a blank line after every statement.
- Leave a blank line after a function's docstring before its implementation.
- Separate a loop from the setup before it and the result handling after it.
  Separate a guard that exits from the work that follows it.
- Use descriptive intermediate variables instead of nesting parsing,
  serialization, result construction and printing in one expression.
- Use keyword arguments for records with several fields. Expand constructors
  and dictionaries when it makes field meanings easier to scan.
- Prefer explicit loops for multi-step processing. Avoid nested comprehensions,
  generator expressions containing business decisions, and lambdas that hide
  validation or selection rules. Simple comprehensions are fine when obvious.
- Keep functions focused, but do not extract trivial helpers solely to meet a
  line-count target or wrap an ordinary operation in another abstraction.
- Explain reasons and non-obvious rules in comments. Do not narrate each
  assignment with a comment.

## Names and type annotations

- Use descriptive `snake_case` names for variables, functions and modules;
  `PascalCase` for classes; and `UPPER_SNAKE_CASE` for constants.
- Annotate function parameters, return values and data-model fields.
- Annotate constants and empty collections when the intended type is not clear
  from the assignment. Allow inference for obvious local values.
- Define reusable type aliases for recurring data shapes. Do not add aliases
  that merely rename a standard type without adding useful meaning.
- Limit `Any` to boundaries where data genuinely has an unknown shape. Narrow
  types after validation and keep dynamic input separate from validated data.
- Compare known model fields through explicit attribute access. Reserve `getattr`
  for genuinely dynamic attribute selection; named field constants do not give
  reflection the static checks available to direct attributes.
- Type annotations and casts support static checking; they do not replace
  runtime validation of external inputs.

For example:

```python
issues: list[ValidationIssue] = []

for violation in validator.iter_errors(parsed):
    issue = issue_from_violation(violation)
    issues.append(issue)

return tuple(issues)
```

## Docstrings

Use Python docstrings with Google-style sections for public APIs and functions
whose behavior is not obvious from their signatures.

- Begin with a short summary of the operation.
- Add `Args:`, `Returns:` and `Raises:` sections when they help explain the API.
- Describe parameter meaning, constraints, side effects and failure conditions.
- Keep types in the signature instead of repeating them throughout the docstring.
- Use a one-line docstring for a straightforward operation; do not add empty or
  repetitive sections just to follow a template.

Example documentation for the contract loader:

```python
"""Load the schema approved for this dataset.

Args:
    schema_path: Path to the versioned extraction schema file.
    expected_sha256: Approved schema hash from the gold manifest.

Returns:
    A contract instance reusable throughout the run.

Raises:
    ContractLoadError: The file cannot be read, its hash differs from the
        approved hash, or the schema is invalid.
"""
```

## Constants and configuration

- Declare constants at module level, outside function and service bodies.
  Use `Final` for bindings that must not be reassigned by application code.
- Keep a constant in its owning module when only that module uses it. Put
  shared constants in a feature-specific module when multiple modules need them.
- Use named constants for significant shared identifiers, filename patterns,
  repeated messages and stable protocol values. Use string enums when a group
  of related machine-readable codes benefits from one named type.
- Keep ordinary one-off messages and self-explanatory protocol keys inline when
  extraction would only add indirection. Do not move every string to constants.
- Use `StrEnum` members consistently for internal state groups used in decisions.
  Keep `Literal` for small value constraints that do not need named runtime
  members, and keep unknown provider finish reasons/error prose as strings.
  Preserve serialized values when migrating an existing group; verify strict
  Python construction and JSON reload behavior separately.
- Model IDs, sampling parameters, URLs, timeouts, retry limits and budgets that
  vary between runs belong in validated configuration/settings.
- `Final` does not enforce runtime immutability or freeze an object's contents.
  Prefer immutable values for shared constants; do not mutate shared definitions.

```python
from typing import Final

SCHEMA_DIALECT: Final[str] = (
    "https://json-schema.org/draft/2020-12/schema"
)
```

## Module responsibilities

- Keep public service APIs focused on coordinating their domain workflow.
- Give cohesive mechanical responsibilities, such as schema loading, strict
  JSON parsing and validation-error translation, descriptive module names.
- Place auxiliary logic with its owner instead of creating a catch-all
  `utils.py`, global constants collection or unrelated helper directory.
- Extract logic when it has a distinct responsibility, meaningful reuse, or
  obscures the main workflow. Avoid one-function wrappers around obvious calls.
- Preserve public behavior, error details and approved contracts during a
  structural refactor. Do not change frozen artifacts to accommodate new code.

## Tests and enforcement

- Manage Python dependency declarations with `uv add` / `uv remove` inside Docker.
  Let uv update `pyproject.toml` and `uv.lock` together; do not hand-edit dependency
  lists or lockfile entries. Pass version constraints to the command when needed.
  Ordinary metadata and tool configuration in `pyproject.toml` remain editable.
  See HW-01's [dependency commands](../hw-01/docs/runtime-validation.md#dependency-maintenance).

- Separate setup, the action under test and assertions with blank lines.
- Name the result before asserting on it; avoid nested calls in assertions.
- Test behavior and meaningful regression risks rather than implementation
  details, spacing, comments or copies of static configuration.
- Start rejection cases from known-valid data and introduce a specific defect.
  Check the failure's stage, keyword and affected path where relevant, rather
  than accepting any failure as evidence for the intended rule.
- Pair important rejection paths with successful cases. Check both exit status
  and output for CLI commands, including the real process entrypoint.
- Keep expected results independent of the implementation under test. Exercise
  artifact checks with changed bytes and validation with invalid contents.
- When auditing test sensitivity, try a bounded set of deliberate defects in
  disposable copies. Report which defects the tests detect; a passing suite or
  a mutation probe does not establish complete correctness.
- Run the homework's documented checks in Docker. For HW-01, use
  `make hw01-check` from the repository root.
- HW-01's enforceable lint, formatting and type rules are configured in
  [`pyproject.toml`](../hw-01/pyproject.toml), with dependencies pinned in its
  lockfile. Ruff and mypy complement this document; passing them alone does
  not establish readability or correctness.
