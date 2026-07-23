"""Demo: LLM tool-calling loop → MCP search_knowledge_base.

Requires MCP server running on MCP_SERVER_URL.

  # Offline (scripted LLM, no API key):
  PYTHONPATH=. python orchestrator/run_demo.py --scripted

  # Live LLM:
  PYTHONPATH=. python orchestrator/run_demo.py --message "What are your branch hours?"
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from orchestrator.llm import LlmTurn, ScriptedProvider, ToolCall
from orchestrator.loop import run_tool_loop
from shared.schemas.mcp import CustomerContext


def main() -> None:
    parser = argparse.ArgumentParser(description="Run LLM ↔ MCP tool loop demo")
    parser.add_argument(
        "--message",
        default="What are your branch hours?",
        help="Customer message",
    )
    parser.add_argument(
        "--intent",
        default=None,
        help="Override intent (default: inferred)",
    )
    parser.add_argument(
        "--scripted",
        action="store_true",
        help="Use a scripted LLM (no LLM_API_KEY required)",
    )
    args = parser.parse_args()

    context = CustomerContext(
        customerId="demo-customer",
        sessionId=f"demo-session-{uuid4().hex[:8]}",
        authToken="demo-token",
        authenticatedAt=datetime.now(timezone.utc),
        channelType="WEB_CHAT",
    )

    llm = None
    if args.scripted:
        llm = ScriptedProvider(
            [
                LlmTurn(
                    tool_calls=[
                        ToolCall(
                            id="call_1",
                            name="search_knowledge_base",
                            arguments={
                                "query": args.message,
                                "searchType": "HYBRID",
                                "maxResults": 3,
                                "minRelevanceScore": 0.1,
                            },
                        )
                    ]
                ),
                LlmTurn(
                    content=(
                        "Our bank branches are open Monday to Friday, 8:00 AM – 5:00 PM (EAT), "
                        "and Saturday 9:00 AM – 1:00 PM. Branches are closed on public holidays."
                    )
                ),
            ]
        )

    result = run_tool_loop(
        args.message,
        customer_context=context,
        intent=args.intent,
        llm=llm,
    )
    print(f"intent={result.intent} rounds={result.rounds} tools={len(result.tool_results)}")
    for item in result.tool_results:
        status = item.status.value if hasattr(item.status, "value") else item.status
        print(f"  tool={item.tool_name} status={status}")
    print()
    print(result.reply)


if __name__ == "__main__":
    main()
