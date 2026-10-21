"""Representative coverage stays bounded, repeatable and distinct from exhaustive checks."""

from dataclasses import replace
from pathlib import Path

import pytest

from extraction_service.preflight import preflight
from extraction_service.record_types import AttemptKind
from extraction_service.runtime.configuration import CapacityScope
from extraction_service.runtime.context import PreparedRequest, prepared_requests
from extraction_service.runtime.selection import select_capacity_requests


def _examples(project: Path, count: int) -> list[PreparedRequest]:
    template = next(prepared_requests(project, preflight(project).experiment))
    result: list[PreparedRequest] = []

    for index in range(count):
        for kind in (AttemptKind.EXTRACTION, AttemptKind.CORRECTION):
            request = template.request.model_copy(update={"source_text": "x" * (1 + index * 10)})
            result.append(replace(template, input_id=f"source-{index}", kind=kind, request=request))

    return result


@pytest.mark.parametrize(
    ("count", "expected_ids"),
    [
        (0, set()),
        (1, {"source-0"}),
        (2, {"source-0", "source-1"}),
        (3, {"source-0", "source-1", "source-2"}),
        (5, {"source-0", "source-2", "source-4"}),
    ],
)
def test_sample_selects_size_extremes_and_middle_with_both_request_kinds(
    project_copy: Path, count: int, expected_ids: set[str]
) -> None:
    requests = _examples(project_copy, count)

    selected = select_capacity_requests(reversed(requests), CapacityScope.REPRESENTATIVE)

    assert {item.input_id for item in selected} == expected_ids
    assert len(selected) == 2 * len(expected_ids)
    assert selected == [item for item in reversed(requests) if item.input_id in expected_ids]

    for input_id in expected_ids:
        kinds = {item.kind for item in selected if item.input_id == input_id}
        assert kinds == {AttemptKind.EXTRACTION, AttemptKind.CORRECTION}


def test_sampling_covers_each_prompt_and_sampling_variant_independently(
    project_copy: Path,
) -> None:
    examples = _examples(project_copy, 5)
    requests: list[PreparedRequest] = []

    for prompt_id in ("prompt-a", "prompt-b"):
        for sampling_id in ("sampling-a", "sampling-b"):
            for item in examples:
                sampling = item.request.sampling.model_copy(update={"id": sampling_id})
                request = item.request.model_copy(update={"sampling": sampling})
                requests.append(replace(item, prompt_id=prompt_id, request=request))

    selected = select_capacity_requests(requests, CapacityScope.REPRESENTATIVE)

    assert len(selected) == 24

    for prompt_id in ("prompt-a", "prompt-b"):
        for sampling_id in ("sampling-a", "sampling-b"):
            group = [
                item
                for item in selected
                if item.prompt_id == prompt_id and item.request.sampling.id == sampling_id
            ]
            assert len(group) == 6
            assert {item.input_id for item in group} == {"source-0", "source-2", "source-4"}


def test_equal_sizes_have_repeatable_selection_independent_of_iteration_order(
    project_copy: Path,
) -> None:
    requests = _examples(project_copy, 5)
    same_size = [
        replace(item, request=item.request.model_copy(update={"source_text": "same size"}))
        for item in requests
    ]

    selected = select_capacity_requests(same_size, CapacityScope.REPRESENTATIVE)
    reversed_selection = select_capacity_requests(reversed(same_size), CapacityScope.REPRESENTATIVE)

    assert {item.input_id for item in selected} == {"source-0", "source-2", "source-4"}
    assert set(selected_item.input_id for selected_item in reversed_selection) == {
        "source-0",
        "source-2",
        "source-4",
    }


def test_exhaustive_selection_keeps_every_request_and_original_order(project_copy: Path) -> None:
    requests = _examples(project_copy, 5)

    selected = select_capacity_requests(iter(requests), CapacityScope.EXHAUSTIVE)

    assert selected == requests
    assert len(selected) == 10
