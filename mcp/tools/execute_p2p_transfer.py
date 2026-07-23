from typing import Any

from mcp.tools.runtime import run_with_db
from services.transaction_service import TransactionService
from shared.schemas.mcp import CustomerContext
from shared.schemas.transaction import ExecuteP2PTransferRequest


class ExecuteP2PTransferTool:
    name = "execute_p2p_transfer"
    description = (
        "Transfer funds from one of the authenticated customer's accounts to another account. "
        "Requires a valid OTP issued for TRANSFER_VERIFICATION purpose."
    )
    state_modifying = True
    authorized_intents = ["FUND_TRANSFER"]

    def run(
        self,
        parameters: dict[str, Any],
        customer_context: CustomerContext | None = None,
    ) -> dict[str, Any]:
        request = ExecuteP2PTransferRequest.model_validate(parameters or {})
        return run_with_db(
            customer_context,
            lambda db, customer_id: TransactionService(db).execute_p2p_transfer(
                customer_id, request
            ),
        )
