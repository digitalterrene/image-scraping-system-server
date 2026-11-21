"""ASGI application entrypoint for local development (Uvicorn) and serverless deployment (Vercel)."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings, get_settings
from app.routers import docs_ui, health, images

OPENAPI_TAGS = [
    {
        "name": "Health",
        "description": "Service discovery (`GET /`) and runtime health / storage telemetry (`GET /health`).",
    },
    {
        "name": "Images",
        "description": (
            "Scrape images from public webpages, list or search stored assets, "
            "stream image files safely, and delete stored images."
        ),
    },
]


def create_app(settings: Settings | None = None) -> FastAPI:
    """Construct and configure the unified FastAPI application."""
    active_settings = settings or get_settings()

    application = FastAPI(
        title=active_settings.app_name,
        version=active_settings.app_version,
        description=(
            "Unified FastAPI service for scraping images from webpages, "
            "storing them safely, searching by filename, and serving image assets.\n\n"
            "**Interactive Tools (no Postman/Thunder Client needed):**\n"
            "- **Visual Playground**: [`/playground`](/playground)\n"
            "- **Scalar API Reference**: [`/scalar`](/scalar)\n"
            "- **Swagger UI**: [`/docs`](/docs)\n"
            "- **ReDoc**: [`/redoc`](/redoc)"
        ),
        openapi_tags=OPENAPI_TAGS,
    )

    if settings is not None:
        application.dependency_overrides[get_settings] = lambda: active_settings

    application.add_middleware(
        CORSMiddleware,
        allow_origins=active_settings.cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(health.router)
    application.include_router(images.router)
    application.include_router(docs_ui.router)

    return application


app = create_app()

# Optional AWS Lambda / Mangum adapter for serverless platforms that require it
try:
    from mangum import Mangum

    handler = Mangum(app)
except ImportError:  # pragma: no cover
    handler = None
