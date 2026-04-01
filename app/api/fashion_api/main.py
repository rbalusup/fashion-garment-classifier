"""FastAPI application factory."""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from fashion_api.config import Settings, get_settings
from fashion_api.db.session import Base, create_db_engine, create_session_factory, get_db_dependency

logger = structlog.get_logger(__name__)


def create_app(settings: Settings | None = None, testing: bool = False) -> FastAPI:
    """Create and configure the FastAPI application.

    Args:
        settings: Override settings (useful for tests).
        testing: When True, uses in-memory SQLite and a temp upload dir.
    """
    if settings is None:
        if testing:
            settings = Settings(  # type: ignore[call-arg]
                anthropic_api_key="test-key",
                fashion_database_url="sqlite:///:memory:",
                fashion_upload_dir="/tmp/fashion_test_uploads",
                fashion_debug=True,
            )
        else:
            settings = get_settings()

    engine = create_db_engine(
        settings.database_url,
        use_static_pool=(settings.database_url == "sqlite:///:memory:"),
    )
    session_factory = create_session_factory(engine)

    def get_db() -> Any:
        yield from get_db_dependency(session_factory)

    @asynccontextmanager
    async def lifespan(app: FastAPI):  # type: ignore[misc]
        # Ensure ORM models are imported so they're registered on Base before create_all
        import fashion_api.db.models  # noqa: F401
        Base.metadata.create_all(bind=engine)
        upload_path = Path(settings.upload_dir)  # type: ignore[union-attr]
        upload_path.mkdir(parents=True, exist_ok=True)
        logger.info("app_started", database_url=settings.database_url)  # type: ignore[union-attr]
        yield
        logger.info("app_shutdown")

    app = FastAPI(
        title="Fashion Garment Classifier",
        version="0.1.0",
        description="AI-powered fashion garment classification and inspiration library",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.state.settings = settings
    app.state.get_db = get_db
    app.state.engine = engine

    @app.get("/health", tags=["health"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    # Routers are registered after DB/settings are wired
    _register_routers(app, settings, get_db)

    # Serve uploaded images as static files
    upload_path = Path(settings.upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=str(upload_path)), name="uploads")

    return app


def _register_routers(app: FastAPI, settings: Settings, get_db: Any) -> None:
    from fashion_api.garment.annotations import make_annotations_router
    from fashion_api.garment.filters import make_filters_router
    from fashion_api.garment.router import make_garment_router

    app.include_router(make_garment_router(settings, get_db), prefix="/api", tags=["garments"])
    app.include_router(make_annotations_router(get_db), prefix="/api", tags=["annotations"])
    app.include_router(make_filters_router(get_db), prefix="/api", tags=["filters"])


# Module-level app for `uvicorn fashion_api.main:app`
app = create_app()
