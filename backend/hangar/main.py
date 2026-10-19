from __future__ import annotations
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .api import (
    actions,
    applications,
    components,
    detect,
    events,
    logs,
    metrics,
    overview,
    ports,
    samples,
    settings,
    ws,
)
from .config import ALLOWED_ORIGINS, APP_NAME, STATIC_DIR, VERSION
from .core.bus import bus
from .core.metrics import metrics_sampler
from .core.supervisor import supervisor
from .db import close_db, init_db
from .security import SecurityGuardMiddleware

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s in %(name)s: %(message)s",
)
logger = logging.getLogger("hangar.main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting %s v%s...", APP_NAME, VERSION)
    await init_db()
    await bus.start()
    await supervisor.start()
    await metrics_sampler.start()
    yield
    # Shutdown
    logger.info("Stopping %s...", APP_NAME)
    await metrics_sampler.stop()
    await supervisor.stop()
    await bus.stop()
    await close_db()


def create_app() -> FastAPI:
    app = FastAPI(
        title=APP_NAME,
        version=VERSION,
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url=None,
    )

    # 1. Custom Security Guard Middleware (Host & Origin & X-Hangar-Client check)
    app.add_middleware(SecurityGuardMiddleware)

    # 2. CORS Middleware with strictly pinned origins (no wildcard *)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(ALLOWED_ORIGINS),
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["*"],
    )

    # 3. Include API Routers under /api
    api_routers = [
        overview.router,
        applications.router,
        components.router,
        actions.router,
        logs.router,
        ports.router,
        events.router,
        metrics.router,
        detect.router,
        settings.router,
        samples.router,
    ]
    for r in api_routers:
        app.include_router(r, prefix="/api")

    # 4. WebSocket route at /ws
    app.include_router(ws.router)

    # 5. Serve Frontend static export if present
    if STATIC_DIR.exists() and (STATIC_DIR / "index.html").exists():
        app.mount("/_next", StaticFiles(directory=str(STATIC_DIR / "_next")), name="next_assets")

        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            requested_file = STATIC_DIR / full_path
            if requested_file.is_file():
                return FileResponse(requested_file)
            index_file = STATIC_DIR / f"{full_path}.html"
            if index_file.is_file():
                return FileResponse(index_file)
            return FileResponse(STATIC_DIR / "index.html")
    else:
        @app.get("/")
        async def root():
            return {
                "name": APP_NAME,
                "version": VERSION,
                "status": "online",
                "docs": "/docs",
                "ui_status": "Frontend not built yet. Run npm run build in frontend directory.",
            }

    return app


app = create_app()

