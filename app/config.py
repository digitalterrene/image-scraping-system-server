"""Application configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent


def _default_storage_dir() -> Path:
    env_dir = os.getenv("SCRAPED_IMAGES_DIR")
    if env_dir:
        return Path(env_dir)
    # Vercel serverless filesystem is read-only outside /tmp
    if os.getenv("VERCEL"):
        return Path("/tmp/scraped_images")
    return BASE_DIR / "scraped_images"


def _parse_cors_origins() -> list[str]:
    raw = os.getenv("CORS_ORIGINS", "*")
    origins = [origin.strip() for origin in raw.split(",") if origin.strip()]
    return origins or ["*"]


@dataclass(frozen=True)
class Settings:
    """Centralized, immutable runtime configuration."""

    app_name: str = "Image Scraping System Server"
    app_version: str = "2.0.0"
    scraped_images_dir: Path = field(default_factory=_default_storage_dir)
    base_url: str | None = field(
        default_factory=lambda: os.getenv("BASE_URL") or None
    )
    request_timeout_seconds: float = field(
        default_factory=lambda: float(os.getenv("REQUEST_TIMEOUT_SECONDS", "15.0"))
    )
    max_concurrent_downloads: int = field(
        default_factory=lambda: int(os.getenv("MAX_CONCURRENT_DOWNLOADS", "10"))
    )
    max_image_size_bytes: int = field(
        default_factory=lambda: int(
            os.getenv("MAX_IMAGE_SIZE_BYTES", str(10 * 1024 * 1024))
        )
    )
    max_images_per_scrape: int = field(
        default_factory=lambda: int(os.getenv("MAX_IMAGES_PER_SCRAPE", "50"))
    )
    cors_origins: list[str] = field(default_factory=_parse_cors_origins)
    user_agent: str = field(
        default_factory=lambda: os.getenv(
            "SCRAPER_USER_AGENT",
            "ImageScrapingSystem/2.0 (+https://github.com/digitalterrene/image-scraping-system-server)",
        )
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached application settings."""
    return Settings()
