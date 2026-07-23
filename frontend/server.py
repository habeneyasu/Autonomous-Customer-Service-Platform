"""FastAPI app serving the ACSP Customer Care web chat."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from frontend.service import chat, create_session, mcp_health

STATIC_DIR = Path(__file__).resolve().parent / "static"


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    session_id: str = Field(min_length=1, max_length=64)
    mode: str = "Demo replies (offline)"
    intent: str = "Auto-detect"


def create_app() -> FastAPI:
    app = FastAPI(title="ACSP Customer Care", docs_url=None, redoc_url=None)

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/api/session")
    def api_session() -> dict:
        return create_session()

    @app.get("/api/health")
    def api_health() -> dict:
        return mcp_health()

    @app.post("/api/chat")
    def api_chat(body: ChatRequest) -> dict:
        try:
            return chat(
                message=body.message,
                session_id=body.session_id,
                mode=body.mode,
                intent=body.intent,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(
                status_code=502,
                detail=f"Request failed. Confirm the MCP server is running. ({exc})",
            ) from exc

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    return app


app = create_app()
