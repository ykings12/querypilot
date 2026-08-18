from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api.routes import connections, eval, health, query, trace
from app.config import get_settings
from app.db.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Warm up metadata DB pool on startup; dispose cleanly on shutdown.
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="QueryPilot API",
        version=__version__,
        description="Secure natural-language-to-SQL developer tool",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(connections.router)
    app.include_router(query.router)
    app.include_router(trace.router)
    app.include_router(eval.router)
    return app


app = create_app()
