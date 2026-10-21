from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import structlog

from app.core.config import get_settings
from app.core.database import init_db, create_tables, close_db
from app.core.telemetry import init_telemetry, shutdown_telemetry
from app.api.routes import router as api_router


structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logger.info("starting_application", app_name=settings.APP_NAME, env=settings.APP_ENV)

    init_db()
    await create_tables()
    init_telemetry(app)

    logger.info("application_started")
    yield

    logger.info("shutting_down_application")
    await close_db()
    shutdown_telemetry()
    logger.info("application_stopped")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        description="OpenShell - Safe, private runtime for autonomous AI agents",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router)

    @app.get("/health", tags=["health"])
    async def health_check():
        return {
            "status": "healthy",
            "version": "1.0.0",
            "environment": settings.APP_ENV,
            "database": "connected",
            "telemetry": "enabled" if settings.OTEL_EXPORTER_OTLP_ENDPOINT else "disabled",
        }

    return app


app = create_app()