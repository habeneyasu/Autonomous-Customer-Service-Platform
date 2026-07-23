"""Launch the ACSP Live Observability Workbench.

Requires MCP for live tool SUCCESS (optional for abuse/tokenization demos):

  PYTHONPATH=. python mcp/run_server.py

Then:

  PYTHONPATH=. python run_dashboard.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import uvicorn


def main() -> None:
    uvicorn.run(
        "workbench.server:app",
        host="127.0.0.1",
        port=7861,
        reload=False,
    )


if __name__ == "__main__":
    main()
