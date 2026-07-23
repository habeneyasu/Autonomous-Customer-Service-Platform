"""Launch the ACSP Customer Care web chat.

Requires MCP server:

  PYTHONPATH=. python mcp/run_server.py

Then:

  PYTHONPATH=. python frontend/run_chat.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import uvicorn


def main() -> None:
    uvicorn.run(
        "frontend.server:app",
        host="127.0.0.1",
        port=7860,
        reload=False,
    )


if __name__ == "__main__":
    main()
