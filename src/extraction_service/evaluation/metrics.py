"""Measured request/accounting metrics with explicit populations and missingness."""

from decimal import Decimal
from math import ceil
from typing import Any

from extraction_service.record_types import AttemptKind, AttemptOutcome, ModelRuntime, RunStatus
from extraction_service.records import RunRecord


def percentile(values: list[float], quantile: float) -> float | None:
    """Use nearest rank, including for small samples; an empty sample stays unknown."""

    if not 0 < quantile <= 1:
        raise ValueError("Percentile quantile must be in (0, 1]")

    if not values:
        return None

    return sorted(values)[ceil(quantile * len(values)) - 1]


def operational_metrics(records: list[RunRecord]) -> dict[str, Any]:
    """Retain all scheduled outcomes; latency/cost scaling uses attempted inputs.

    Missing paid charges are unknown, not free. Known charges are a lower bound;
    reservations are reported separately and never substituted for actual cost.
    Local API charges are zero, excluding machine/electricity/time costs.
    """

    attempted = [record for record in records if record.attempts]
    durations = [record.duration_ms for record in attempted]
    attempts = [attempt for record in records for attempt in record.attempts]
    corrected = sum(any(a.kind == AttemptKind.CORRECTION for a in r.attempts) for r in records)
    first_valid = sum(
        bool(record.attempts) and record.attempts[0].outcome == AttemptOutcome.VALID
        for record in records
    )
    final_valid = sum(record.status == RunStatus.SUCCEEDED for record in records)
    known = Decimal("0")
    unknown = 0

    for attempt in attempts:
        if attempt.runtime != ModelRuntime.OPENROUTER:
            continue

        if attempt.cost_usd is None:
            unknown += 1
        else:
            known += Decimal(str(attempt.cost_usd))

    cost = None if unknown else known
    reserved = sum(
        (
            Decimal(str(attempt.budget_reserved_usd))
            for attempt in attempts
            if attempt.runtime == ModelRuntime.OPENROUTER
            and attempt.budget_reserved_usd is not None
        ),
        start=Decimal("0"),
    )
    scaled = None if cost is None or not attempted else cost * 1000 / len(attempted)
    selected = len(records)

    return {
        "selected_inputs": selected,
        "attempted_inputs": len(attempted),
        "not_attempted_inputs": sum(record.status == RunStatus.NOT_ATTEMPTED for record in records),
        "physical_requests": len(attempts),
        "first_valid": first_valid,
        "final_valid": final_valid,
        "first_valid_rate": None if not selected else first_valid / selected,
        "final_valid_rate": None if not selected else final_valid / selected,
        "corrected_inputs": corrected,
        "correction_rate": None if not selected else corrected / selected,
        "latency_sample_count": len(durations),
        "latency_population": "attempted-input-end-to-end",
        "latency_percentile_method": "nearest-rank",
        "latency_p50_ms": percentile(durations, 0.50),
        "latency_p95_ms": percentile(durations, 0.95),
        "known_api_cost_usd": str(known),
        "reserved_api_cost_usd": str(reserved),
        "unknown_cost_requests": unknown,
        "total_api_cost_usd": None if cost is None else str(cost),
        "api_cost_per_1000_attempted_inputs_usd": None if scaled is None else str(scaled),
        "cost_population": "attempted-inputs-including-retries-corrections-and-failures",
        "local_machine_costs_included": False,
    }
