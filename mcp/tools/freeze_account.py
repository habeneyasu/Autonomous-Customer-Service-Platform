from typing import Any

from mcp.tools.runtime import run_with_db
from services.account_service import AccountService
from shared.schemas.account import FreezeAccountRequest
from shared.schemas.mcp import CustomerContext


class FreezeAccountTool:
    name = "freeze_account"
    description = (
        "Freeze one of the authenticated customer's accounts. "
        "Requires a valid OTP issued for ACCOUNT_FREEZE purpose."
    )
    state_modifying = True
    authorized_intents = ["ACCOUNT_MANAGEMENT"]

    def run(
        self,
        parameters: dict[str, Any],
        customer_context: CustomerContext | None = None,
    ) -> dict[str, Any]:
        request = FreezeAccountRequest.model_validate(parameters or {})
        return run_with_db(
            customer_context,
            lambda db, customer_id: AccountService(db).freeze_account(customer_id, request),
            by_alias=True,
        )
