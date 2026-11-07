"""Strict, hash-bound offline comparison protocols; never execution permission."""

from pathlib import Path
from typing import Any, Literal, Self

from pydantic import Field, model_validator

from extraction_service.application.persistence import item_key, reload_records
from extraction_service.archiving.archive import load_index
from extraction_service.archiving.bundles import verify_bundle
from extraction_service.archiving.files import confined, digest, read_json, regular_bytes
from extraction_service.corpus.loading import load_corpus
from extraction_service.runtime_types import Identifier, PositiveInt, Sha256, StrictModel


class Binding(StrictModel):
    path: str
    sha256: Sha256

    def verify(self, project: Path) -> Path:
        """Reject changed files and symlinks without interpreting their contents."""

        path = confined(project, self.path)
        regular_bytes(path)
        if digest(path) != self.sha256:
            raise ValueError("Protocol artifact hash differs")

        return path


class RunBinding(StrictModel):
    manifest_sha256: Sha256
    original_execution: dict[str, Any]
    records: dict[Identifier, Sha256]


class Selection(StrictModel):
    comparison_controls: dict[str, Any]
    identity: dict[str, Any]
    runs: dict[Identifier, RunBinding]


class Limits(StrictModel):
    model_calls: Literal[0]
    generated_tokens: Literal[0]
    additional_api_spend_usd: Literal["0"]
    analysis_seconds: PositiveInt
    verification_seconds: PositiveInt


class Thresholds(StrictModel):
    selected_cases_per_side: PositiveInt
    gold_cases_per_side: PositiveInt
    required_controls: Literal[16]
    accepted_bad_controls: Literal[0]
    historical_observations: Literal[240]


class EvaluationProtocol(StrictModel):
    version: Literal["evaluation-protocol-v2", "evaluation-protocol-v3"]
    experiment_id: Identifier
    frozen_at: str
    source_revision: str
    status: str
    question: str
    claim_scope: str
    allowed_differences: list[str]
    automatic_reruns: Literal[False]
    archive: Binding
    corpus: Binding
    gold_manifest: Binding
    schema_binding: Binding = Field(alias="schema")
    exposure: Binding
    rubric: Binding
    controls: Binding
    control_suite: Binding | None = None
    public_budget_policy: Binding
    plan_snapshot_sha256: Sha256
    controls_authority: str
    revision_reason: str
    rubric_status: str
    input_ids: list[Identifier]
    gold_input_ids: list[Identifier]
    selections: dict[str, Selection]
    limits: Limits
    thresholds: Thresholds
    output: str

    @model_validator(mode="after")
    def check_population(self) -> Self:
        """Do not permit selective intersections or widened normalization rules."""

        if self.allowed_differences != ["prompt_id", "prompt_sha256", "collection time"]:
            raise ValueError("Only the declared prompt intervention is permitted")
        if self.version == "evaluation-protocol-v3" and self.control_suite is None:
            raise ValueError("Executable protocol requires a bound control suite")
        if set(self.selections) != {"v1", "v2"}:
            raise ValueError("Protocol requires both named sides")
        for ids, count in (
            (self.input_ids, self.thresholds.selected_cases_per_side),
            (self.gold_input_ids, self.thresholds.gold_cases_per_side),
        ):
            if len(ids) != count or len(set(ids)) != count:
                raise ValueError("Protocol population differs or contains duplicates")
        if not set(self.gold_input_ids) <= set(self.input_ids):
            raise ValueError("Gold population is outside selected inputs")
        controls = []
        for selection in self.selections.values():
            members = [name for run in selection.runs.values() for name in run.records]
            if len(members) != len(self.input_ids) or set(members) != set(self.input_ids):
                raise ValueError("Side membership differs or overlaps")
            identity = dict(selection.identity)
            identity.pop("prompt_id", None)
            identity.pop("prompt_sha256", None)
            if identity != selection.comparison_controls:
                raise ValueError("Declared comparison controls differ from identity")
            controls.append(identity)
        if controls[0] != controls[1]:
            raise ValueError("Non-permitted control differences")
        if not self.output.startswith("results/submission/"):
            raise ValueError("Analysis output must stay in submission results")

        return self


def load_protocol(project: Path, filename: str) -> EvaluationProtocol:
    """Validate declarations before reading run evidence or producing analysis."""

    path = confined(project, filename)
    read_json(path)  # Reject duplicate JSON keys before Pydantic parsing.
    protocol = EvaluationProtocol.model_validate_json(regular_bytes(path))
    for binding in (
        protocol.archive,
        protocol.corpus,
        protocol.gold_manifest,
        protocol.schema_binding,
        protocol.exposure,
        protocol.rubric,
        protocol.controls,
        protocol.public_budget_policy,
    ):
        binding.verify(project)
    if protocol.control_suite is not None:
        protocol.control_suite.verify(project)
    corpus = load_corpus(project)
    if set(protocol.input_ids) != {source.input_id for source in corpus.inputs}:
        raise ValueError("Selected inputs differ from the approved corpus")
    if set(protocol.gold_input_ids) != set(corpus.gold):
        raise ValueError("Gold selection differs from approved labels")
    if protocol.schema_binding.sha256 != corpus.contract.identity.sha256:
        raise ValueError("Schema differs from approved contract")
    exposure = read_json(confined(project, protocol.exposure.path))
    if (
        exposure.get("version") != "evaluation-exposure-v1"
        or exposure.get("corpus") != protocol.corpus.model_dump()
    ):
        raise ValueError("Exposure version or corpus binding differs")
    cases = exposure["cases"]
    if len(cases) != len(protocol.input_ids) or {c["input_id"] for c in cases} != set(
        protocol.input_ids
    ):
        raise ValueError("Exposure inventory is incomplete or duplicated")
    sources = {source.input_id: source for source in corpus.inputs}
    for case in cases:
        source_case = sources[case["input_id"]]
        expected_label = "human_approved" if source_case.is_gold else "not_gold"
        if (
            case["source_group"] != source_case.source_group
            or case["layout_group"] != source_case.layout_group
            or case["label_status"] != expected_label
        ):
            raise ValueError("Exposure grouping or label authority differs")
        if (
            case["independent_holdout"]
            or case["input_sha256"] != sources[case["input_id"]].input_sha256
        ):
            raise ValueError("Exposure claims differ from development corpus")
    rubric = read_json(confined(project, protocol.rubric.path))
    if rubric.get("version") != "evaluation-rubric-v1":
        raise ValueError("Unsupported review rubric")
    for rule in (
        "source_support_is_output_correctness",
        "evaluation_is_permission_to_apply",
        "invalid_output_matches_gold_null",
        "schema_validity_implies_truth",
        "automatic_semantic_repair",
    ):
        if rubric.get(rule) is not False:
            raise ValueError("Rubric weakens evaluation authority")
    confined(project, protocol.output)

    return protocol


def verify_sources(project: Path, protocol: EvaluationProtocol, source: str) -> None:
    """Bind exact original run bundles and record populations to the archive index."""

    index = load_index(confined(project, protocol.archive.path))
    archived = {bundle.name: bundle for bundle in index.bundles}
    source_root = confined(project, source)
    for selection in protocol.selections.values():
        for name, expected in selection.runs.items():
            directory = confined(source_root, name)
            bundle = verify_bundle(directory)
            if (
                archived.get(name) != bundle
                or digest(directory / "manifest.json") != expected.manifest_sha256
            ):
                raise ValueError("Run differs from the pinned archive/protocol")
            manifest, records = reload_records(directory)
            if manifest.experiment.execution.model_dump() != expected.original_execution:
                raise ValueError("Original execution policy differs")
            if {r.input_id for r in records} != set(expected.records) or len(records) != len(
                expected.records
            ):
                raise ValueError("Run record population differs")
            for record in records:
                key = item_key(
                    record.input_id, record.model_id, record.prompt_id, record.sampling_id
                )
                if manifest.record_sha256[key] != expected.records[record.input_id]:
                    raise ValueError("Selected record hash differs")
