"""Select bounded setup examples without claiming a byte count bounds model tokens."""

from collections.abc import Iterable

from extraction_service.record_types import AttemptKind
from extraction_service.runtime.configuration import CapacityScope
from extraction_service.runtime.context import PreparedRequest


def _message_size(prepared: PreparedRequest) -> tuple[int, str]:

    return prepared.message_utf8_bytes(), prepared.input_id


def select_capacity_requests(
    requests: Iterable[PreparedRequest], scope: CapacityScope
) -> list[PreparedRequest]:
    """Sample smallest, middle and largest initial messages per prompt/sampling pair.

    Include both initial and correction fixtures for each selected document.
    Byte size provides a repeatable spread of examples, never a token bound.
    Preserve corpus order in the returned selection and deduplicate small corpora.
    """

    prepared = list(requests)

    if scope == CapacityScope.EXHAUSTIVE:
        return prepared

    groups: dict[tuple[str, str], list[PreparedRequest]] = {}

    for item in prepared:
        if item.kind == AttemptKind.EXTRACTION:
            variant = (item.prompt_id, item.request.sampling.id)
            groups.setdefault(variant, []).append(item)

    selected: set[tuple[str, str, str]] = set()

    for (prompt_id, sampling_id), initial_requests in groups.items():
        ordered = sorted(initial_requests, key=_message_size)
        positions = (0, len(ordered) // 2, len(ordered) - 1)

        for position in positions:
            selected.add((prompt_id, sampling_id, ordered[position].input_id))

    result: list[PreparedRequest] = []

    for item in prepared:
        identity = (item.prompt_id, item.request.sampling.id, item.input_id)

        if identity in selected:
            result.append(item)

    return result
