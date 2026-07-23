"""FastAPI Live Observability Workbench."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from workbench.scenarios import SCENARIOS, run_scenario

STATIC_DIR = Path(__file__).resolve().parent / "static"


def create_app() -> FastAPI:
    app = FastAPI(title="ACSP Live Observability Workbench", docs_url=None, redoc_url=None)

    @app.get("/")
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    @app.get("/api/scenarios")
    def list_scenarios() -> dict:
        return {
            key: {"title": cfg["title"], "intent": cfg["intent"], "message": cfg["message"]}
            for key, cfg in SCENARIOS.items()
        }

    @app.post("/api/scenarios/{key}/run")
    def run(key: str) -> dict:
        if key not in SCENARIOS:
            raise HTTPException(status_code=404, detail=f"Unknown scenario: {key}")
        try:
            return run_scenario(key).to_dict()
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    return app


app = create_app()
