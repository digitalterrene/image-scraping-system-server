"""Unified image scraping, listing, searching, serving, and deletion endpoints."""

from __future__ import annotations

from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import FileResponse

from app.config import Settings, get_settings
from app.schemas import (
    DeleteResponse,
    FailedImage,
    ImageInfo,
    ImageListResponse,
    ImageSearchResponse,
    ScrapeRequest,
    ScrapeResponse,
)
from app.services.scraper import ImageScraperService, WebpageFetchError
from app.services.storage import ImageStorage, InvalidFilenameError

router = APIRouter(prefix="/api/v1/images", tags=["Images"])


def get_storage(settings: Settings = Depends(get_settings)) -> ImageStorage:
    """Dependency provider for the local image storage backend."""
    return ImageStorage(settings.scraped_images_dir)


def get_scraper_service(
    settings: Settings = Depends(get_settings),
    storage: ImageStorage = Depends(get_storage),
) -> ImageScraperService:
    """Dependency provider for the image scraping service."""
    return ImageScraperService(storage=storage, settings=settings)


def _build_image_url(request: Request, settings: Settings, filename: str) -> str:
    encoded_name = quote(filename)
    if settings.base_url:
        return f"{settings.base_url.rstrip('/')}/{encoded_name}"
    base = str(request.base_url).rstrip("/")
    return f"{base}/api/v1/images/{encoded_name}"


def _to_image_info(request: Request, settings: Settings, path: Path) -> ImageInfo:
    return ImageInfo(
        filename=path.name,
        url=_build_image_url(request, settings, path.name),
        size_bytes=path.stat().st_size,
    )


@router.post(
    "/scrape",
    response_model=ScrapeResponse,
    status_code=status.HTTP_200_OK,
    summary="Scrape images from a webpage URL",
    responses={
        400: {"description": "Upstream webpage could not be fetched (network error, timeout, or non-2xx response)."},
        404: {"description": "Webpage loaded, but no valid <img> URLs were found."},
        422: {"description": "Invalid request payload (e.g., non-HTTP/HTTPS URL scheme)."},
        502: {"description": "Images were discovered, but none could be downloaded or validated."},
    },
)
async def scrape_images(
    payload: ScrapeRequest,
    request: Request,
    settings: Settings = Depends(get_settings),
    scraper: ImageScraperService = Depends(get_scraper_service),
) -> ScrapeResponse:
    """Fetch a webpage, extract all image URLs, download valid images, and return metadata."""
    try:
        result = await scraper.scrape_page(str(payload.url))
    except WebpageFetchError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if result.total_found == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No images found on the target webpage.",
        )

    if not result.saved_paths:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Images were discovered on the webpage, but none could be downloaded.",
        )

    saved_images = [
        _to_image_info(request, settings, path) for path in result.saved_paths
    ]
    failed_images = [
        FailedImage(source_url=item.source_url, reason=item.reason)
        for item in result.failed
    ]

    return ScrapeResponse(
        message="Images scraped and saved successfully.",
        source_url=result.source_url,
        total_found=result.total_found,
        saved_count=len(saved_images),
        failed_count=len(failed_images),
        saved_images=saved_images,
        failed_images=failed_images,
    )


@router.get(
    "",
    response_model=ImageListResponse,
    summary="List all stored images (with optional search filter)",
)
async def list_images(
    request: Request,
    query: str | None = Query(
        default=None,
        description="Optional case-insensitive substring filter applied to filenames.",
    ),
    settings: Settings = Depends(get_settings),
    storage: ImageStorage = Depends(get_storage),
) -> ImageListResponse:
    """Return metadata and URLs for all stored images, optionally filtered by `query`."""
    paths = storage.list_images(query=query)
    images = [_to_image_info(request, settings, path) for path in paths]
    return ImageListResponse(count=len(images), images=images)


@router.get(
    "/search",
    response_model=ImageSearchResponse,
    summary="Search stored images by filename",
)
async def search_images(
    request: Request,
    query: str = Query(
        ...,
        min_length=1,
        description="Case-insensitive substring to match against stored image filenames.",
    ),
    settings: Settings = Depends(get_settings),
    storage: ImageStorage = Depends(get_storage),
) -> ImageSearchResponse:
    """Search stored images by filename substring. Returns 404 when no images match."""
    cleaned_query = query.strip()
    if not cleaned_query:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty.",
        )

    paths = storage.list_images(query=cleaned_query)
    if not paths:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No matching images found for query '{cleaned_query}'.",
        )

    matching = [_to_image_info(request, settings, path) for path in paths]
    return ImageSearchResponse(
        query=cleaned_query,
        count=len(matching),
        matching_images=matching,
    )


@router.get(
    "/{filename}",
    summary="Retrieve a specific stored image",
)
async def get_image(
    filename: str,
    storage: ImageStorage = Depends(get_storage),
) -> FileResponse:
    """Serve a stored image file safely with path-traversal protection."""
    try:
        file_path = storage.get_image_path(filename)
    except InvalidFilenameError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if file_path is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found.",
        )

    return FileResponse(file_path)


@router.delete(
    "/{filename}",
    response_model=DeleteResponse,
    summary="Delete a specific stored image",
)
async def delete_image(
    filename: str,
    storage: ImageStorage = Depends(get_storage),
) -> DeleteResponse:
    """Delete a stored image file by filename."""
    try:
        deleted = storage.delete_image(filename)
    except InvalidFilenameError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Image not found.",
        )

    return DeleteResponse(message="Image deleted successfully.", filename=filename)
