"""FastAPI entry point for the Prepped local application."""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from prepped.database import initialize_database
from prepped.scenarios import DEFAULT_SCENARIO_PATH, ScenarioValidationError, load_scenario


ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = ROOT / "data" / "prepped.sqlite3"
INDEX_PATH = ROOT / "static" / "index.html"


def create_app(
    db_path: Path = DEFAULT_DB_PATH,
    scenario_path: Path = DEFAULT_SCENARIO_PATH,
) -> FastAPI:
    """Build an app with injectable local paths for isolated tests."""

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        initialize_database(Path(db_path))
        yield

    application = FastAPI(
        title="Prepped",
        description="A local-first scenario practice prototype.",
        version="0.1.0",
        lifespan=lifespan,
    )

    application.mount("/static", StaticFiles(directory=ROOT / "static"), name="static")

    @application.get("/", include_in_schema=False)
    def home() -> FileResponse:
        return FileResponse(INDEX_PATH)

    @application.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "application": "Prepped"}

    @application.get("/api/scenarios/project-explanation")
    def project_explanation_scenario() -> dict[str, Any]:
        try:
            return load_scenario(Path(scenario_path))
        except ScenarioValidationError as exc:
            raise HTTPException(status_code=500, detail=f"Scenario configuration error: {exc}") from exc

    return application


app = create_app()
