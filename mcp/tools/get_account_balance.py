from typing import Any

from services.account_service import AccountService
from mcp.tools.runtime import run_with_db
from shared.schemas.mcp import CustomerContext


class GetAccountBalanceTool:
    name = "get_account_balance"
    description = "Return balances for the authenticated customer's accounts."
    state_modifying = False
    authorized_intents = ["BALANCE_INQUIRY", "FUND_TRANSFER"]

    def run(
        self,
        parameters: dict[str, Any],
        customer_context: CustomerContext | None = None,
    ) -> dict[str, Any]:
        _ = parameters
        return run_with_db(
            customer_context,
            lambda db, customer_id: AccountService(db).get_balance_by_customer(customer_id),
        )
