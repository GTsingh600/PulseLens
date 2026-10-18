"""FastAPI entry point: `uvicorn pulselens.api.main:app`.

M1.1 exposes only `/api/health`. Session, console and WebSocket routers (M1.2, M3.x) are added
with `app.include_router(...)` in `create_app`.
"""

from __future__ import annotations

from fastapi import FastAPI

from pulselens import __version__
from pulselens.config import data_dir, get_config
from pulselens.models import HealthResponse
from pulselens.store import SessionStore


def create_app(store: SessionStore | None = None) -> FastAPI:
    get_config()  # fail fast on a bad config.yaml
    app = FastAPI(title="PulseLens", version=__version__)
    app.state.store = store or SessionStore(data_dir())

    @app.get("/api/health", response_model=HealthResponse)
    def health() -> HealthResponse:
        return HealthResponse(status="ok", service="pulselens", version=__version__)

    return app


app = create_app()
