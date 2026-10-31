"""Independent cost oracles and read-only offline planning."""

import json
from decimal import Decimal

import pytest

from .conftest import ControlledService

INPUT = "B02-S003-PO01"


def test_nonzero_estimate_includes_all_physical_requests(service: ControlledService) -> None:
    service.coverage([INPUT])
    path = service.project / "config/coverage.json"
    coverage = json.loads(path.read_bytes())
    coverage["provider"]["pricing"]["request_usd"] = "0.001"
    path.write_text(json.dumps(coverage))

    result = service.invoke(
        "plan-run", "--model", "provider", "--input", INPUT, "--coverage", "config/coverage.json"
    )

    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    # Four physical requests, each covering full input/output allowances plus a fee.
    assert report["maximum_physical_requests"] == 4
    assert Decimal(report["maximum_api_usd_by_model"]["provider"]) == Decimal("0.0203840")
    assert service.requests == []
    assert not (service.project / "results/budget-ledger.json").exists()


@pytest.mark.parametrize("defect", ["model", "provider", "runtime", "output"])
def test_incompatible_coverage_is_unverified(service: ControlledService, defect: str) -> None:
    service.coverage([INPUT])
    path = service.project / "config/coverage.json"
    coverage = json.loads(path.read_bytes())
    pricing = coverage["provider"]["pricing"]

    if defect == "model":
        pricing["dependency"]["model_name"] = "another-model"
    elif defect == "provider":
        pricing["dependency"]["serving_provider"] = "another-provider"
    elif defect == "runtime":
        pricing["dependency"]["runtime"] = "ollama-native"
        pricing["dependency"]["serving_provider"] = None
        pricing["dependency"]["runtime_version"] = "test"
        pricing["dependency"]["model_digest"] = "a" * 64
    else:
        pricing["output_token_ceiling"] = 4095

    path.write_text(json.dumps(coverage))

    result = service.invoke(
        "plan-run", "--model", "provider", "--input", INPUT, "--coverage", "config/coverage.json"
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["maximum_api_usd_by_model"] == {"provider": None}
    assert service.requests == []


def test_plan_reopens_prior_accounting_without_writing(service: ControlledService) -> None:
    initialized = service.invoke(
        "budget-init", "--opening-spend", "0.23", "--evidence", "Controlled prior spend"
    )
    assert initialized.returncode == 0
    ledger = service.project / "results/budget-ledger.json"
    before = ledger.read_bytes()

    result = service.invoke("plan-run", "--model", "provider", "--input", INPUT)

    assert result.returncode == 0
    assert Decimal(json.loads(result.stdout)["accounted_prior_usd"]) == Decimal("0.23")
    assert ledger.read_bytes() == before
    assert service.requests == []
