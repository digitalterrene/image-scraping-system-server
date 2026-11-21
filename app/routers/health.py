"""Root discovery and health-check endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Request

from app.config import Settings, get_settings
from app.schemas import HealthResponse
from app.services.storage import ImageStorage

router = APIRouter(tags=["Health"])


def get_storage(settings: Settings = Depends(get_settings)) -> ImageStorage:
    """Dependency provider for image storage."""
    return ImageStorage(settings.scraped_images_dir)


@router.get("/", summary="Service discovery")
async def root(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> dict[str, object]:
    """Return service metadata and primary API routes."""
    base = str(request.base_url).rstrip("/")
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "interactive_docs": {
            "playground": f"{base}/playground",
            "swagger_ui": f"{base}/docs",
            "scalar": f"{base}/scalar",
            "redoc": f"{base}/redoc",
            "openapi_json": f"{base}/openapi.json",
        },
        "endpoints": {
            "health": "/health",
            "scrape": "/api/v1/images/scrape",
            "list_images": "/api/v1/images",
            "search_images": "/api/v1/images/search",
            "get_image": "/api/v1/images/{filename}",
            "delete_image": "/api/v1/images/{filename}",
        },
    }


@router.get("/health", response_model=HealthResponse, summary="Health check")
async def health_check(
    settings: Settings = Depends(get_settings),
    storage: ImageStorage = Depends(get_storage),
) -> HealthResponse:
    """Report service health and current local storage status."""
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        storage_dir=str(storage.base_dir),
        stored_images_count=storage.count_images(),
    )
