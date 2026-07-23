"""Run the MCP HTTP server (default port 8001)."""

import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import uvicorn

from shared.config.settings import get_settings
from shared.logging.setup import configure_logging


def main() -> None:
    configure_logging()
    settings = get_settings()
    parsed = urlparse(settings.mcp_server_url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or 8001

    uvicorn.run(
        "mcp.server:app",
        host=host,
        port=port,
        reload=settings.debug,
    )


if __name__ == "__main__":
    main()
