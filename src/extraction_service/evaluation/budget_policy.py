"""Public, manifest-bound permission to group historical evaluation policies.

This record supports read-only evaluation. It is neither a spending ledger nor
authority to execute requests, resolve unknown charges or change live budgets.
"""

from decimal import Decimal
from typing import Literal, Self

from pydantic import Field, model_validator

from extraction_service.execution.budget.ledger import BudgetRevision
from extraction_service.execution.budget.pricing import Money
from extraction_service.runtime_types import Identifier, Sha256, StrictModel


class EvaluationBudgetPolicy(StrictModel):
    """Retain a reviewed cap-raise chain and bind its use to exact manifests."""

    version: Literal["evaluation-budget-policy-v1"] = "evaluation-budget-policy-v1"
    source_archive_sha256: Sha256
    evidence_bundle: Identifier
    budget_usd: Money
    matrix_reserve_usd: Money
    policy_revisions: list[BudgetRevision] = Field(min_length=1)
    manifests: dict[Identifier, Sha256] = Field(min_length=1)

    @model_validator(mode="after")
    def check_chain(self) -> Self:
        previous = self.policy_revisions[0].previous_budget_usd

        if not Decimal("0") <= self.matrix_reserve_usd < previous:
            raise ValueError("Evaluation reserve must stay below every historical cap")

        for revision in self.policy_revisions:
            if revision.previous_budget_usd != previous or revision.budget_usd <= previous:
                raise ValueError("Evaluation cap revision chain is discontinuous or not increasing")

            previous = revision.budget_usd

        if previous != self.budget_usd:
            raise ValueError("Evaluation revision chain differs from its final cap")

        return self

    def check_manifest(self, run_id: str, sha256: str) -> None:
        """Prevent an opt-in grouping record from covering new or changed runs."""

        if self.manifests.get(run_id) != sha256:
            raise ValueError("Run manifest is outside the public evaluation policy")
