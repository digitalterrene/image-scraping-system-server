"""Pydantic request and response schemas for the API."""

from __future__ import annotations

from pydantic import AnyHttpUrl, BaseModel, Field


class ScrapeRequest(BaseModel):
    """Request payload for scraping images from a target webpage."""

    url: AnyHttpUrl = Field(
        ...,
        description="Public HTTP or HTTPS URL of the webpage to scrape images from.",
        examples=["https://example.com"],
    )


class ImageInfo(BaseModel):
    """Metadata describing a stored image resource."""

    filename: str = Field(..., description="Sanitized filename in local storage.")
    url: str = Field(..., description="Public URL to retrieve the image.")
    size_bytes: int = Field(..., ge=0, description="File size in bytes.")


class FailedImage(BaseModel):
    """Details about an image URL that could not be downloaded or validated."""

    source_url: str = Field(..., description="Original image URL discovered on the page.")
    reason: str = Field(..., description="Human-readable explanation of the failure.")


class ScrapeResponse(BaseModel):
    """Summary returned after a webpage scraping operation."""

    message: str
    source_url: str
    total_found: int = Field(..., ge=0)
    saved_count: int = Field(..., ge=0)
    failed_count: int = Field(..., ge=0)
    saved_images: list[ImageInfo]
    failed_images: list[FailedImage] = Field(default_factory=list)


class ImageListResponse(BaseModel):
    """Collection response for listing stored images."""

    count: int = Field(..., ge=0)
    images: list[ImageInfo]


class ImageSearchResponse(BaseModel):
    """Search response for filename-matched images."""

    query: str
    count: int = Field(..., ge=0)
    matching_images: list[ImageInfo]


class DeleteResponse(BaseModel):
    """Confirmation payload after deleting an image."""

    message: str
    filename: str


class HealthResponse(BaseModel):
    """Service health and storage telemetry."""

    status: str
    version: str
    storage_dir: str
    stored_images_count: int = Field(..., ge=0)
