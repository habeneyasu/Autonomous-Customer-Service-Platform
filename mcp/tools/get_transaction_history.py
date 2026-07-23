from typing import Any

from mcp.tools.runtime import run_with_db
from services.transaction_service import TransactionService
from shared.schemas.mcp import CustomerContext
from shared.schemas.transaction import TransactionHistoryRequest


class GetTransactionHistoryTool:
    name = "get_transaction_history"
    description = (
        "Retrieve recent transactions across the authenticated customer's accounts. "
        "Supports optional pagination via limit and offset."
    )
    state_modifying = False
    authorized_intents = ["TRANSACTION_HISTORY"]

    def run(
        self,
        parameters: dict[str, Any],
        customer_context: CustomerContext | None = None,
    ) -> dict[str, Any]:
        request = TransactionHistoryRequest.model_validate(parameters or {})
        return run_with_db(
            customer_context,
            lambda db, customer_id: TransactionService(db).get_transaction_history_by_customer_id(
                customer_id,
                limit=request.limit,
                offset=request.offset,
            ),
            by_alias=True,
        )
