from mcp.tools.execute_p2p_transfer import ExecuteP2PTransferTool
from mcp.tools.freeze_account import FreezeAccountTool
from mcp.tools.get_account_balance import GetAccountBalanceTool
from mcp.tools.get_transaction_history import GetTransactionHistoryTool
from mcp.tools.search_knowledge_base import SearchKnowledgeBaseTool

DEFAULT_TOOLS = (
    SearchKnowledgeBaseTool(),
    GetAccountBalanceTool(),
    GetTransactionHistoryTool(),
    FreezeAccountTool(),
    ExecuteP2PTransferTool(),
)

__all__ = [
    "DEFAULT_TOOLS",
    "ExecuteP2PTransferTool",
    "FreezeAccountTool",
    "GetAccountBalanceTool",
    "GetTransactionHistoryTool",
    "SearchKnowledgeBaseTool",
]
