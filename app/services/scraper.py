"""Asynchronous webpage image scraping and concurrent download service."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from app.config import Settings
from app.services.storage import ImageStorage

_CONTENT_TYPE_TO_EXT: dict[str, str] = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/svg+xml": ".svg",
    "image/avif": ".avif",
    "image/x-icon": ".ico",
    "image/vnd.microsoft.icon": ".ico",
    "image/bmp": ".bmp",
}


class WebpageFetchError(RuntimeError):
    """Raised when the target webpage cannot be fetched."""


@dataclass
class FailedDownload:
    """Represents a single failed image download."""

    source_url: str
    reason: str


@dataclass
class ScrapeResult:
    """Aggregated outcome of scraping a webpage."""

    source_url: str
    total_found: int
    saved_paths: list[Path] = field(default_factory=list)
    failed: list[FailedDownload] = field(default_factory=list)


def extract_image_urls(html: str, page_url: str, max_images: int = 50) -> list[str]:
    """Parse HTML and return deduplicated absolute HTTP(S) image URLs."""
    soup = BeautifulSoup(html, "html.parser")
    seen: set[str] = set()
    urls: list[str] = []

    for img in soup.find_all("img"):
        raw_src = (img.get("src") or img.get("data-src") or "").strip()
        if not raw_src or raw_src.startswith("data:"):
            continue

        absolute_url = urljoin(page_url, raw_src)
        parsed = urlparse(absolute_url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            continue

        if absolute_url not in seen:
            seen.add(absolute_url)
            urls.append(absolute_url)
            if len(urls) >= max_images:
                break

    return urls


def derive_filename(image_url: str, content_type: str, index: int) -> str:
    """Derive a safe filename from an image URL and its HTTP Content-Type."""
    parsed_path = urlparse(image_url).path
    raw_name = Path(parsed_path).name
    mime_type = content_type.split(";")[0].strip().lower()
    fallback_ext = _CONTENT_TYPE_TO_EXT.get(mime_type, ".img")
    return ImageStorage.sanitize_filename(
        raw_name,
        fallback_stem=f"image_{index}",
        fallback_ext=fallback_ext,
    )


class ImageScraperService:
    """Fetches a webpage and concurrently downloads discovered images into storage."""

    def __init__(
        self,
        storage: ImageStorage,
        settings: Settings,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.storage = storage
        self.settings = settings
        self._injected_client = http_client

    async def _download_single(
        self,
        client: httpx.AsyncClient,
        semaphore: asyncio.Semaphore,
        image_url: str,
        index: int,
    ) -> tuple[Path | None, FailedDownload | None]:
        async with semaphore:
            try:
                response = await client.get(image_url)
            except httpx.HTTPError as exc:
                return None, FailedDownload(source_url=image_url, reason=f"HTTP error: {exc}")

            if response.status_code != 200:
                return None, FailedDownload(
                    source_url=image_url,
                    reason=f"Non-200 status code ({response.status_code})",
                )

            content_type = response.headers.get("content-type", "")
            if not content_type.lower().startswith("image/"):
                return None, FailedDownload(
                    source_url=image_url,
                    reason=f"Unsupported content-type: {content_type or 'missing'}",
                )

            data = response.content
            if len(data) > self.settings.max_image_size_bytes:
                return None, FailedDownload(
                    source_url=image_url,
                    reason=f"Image exceeds max size limit ({self.settings.max_image_size_bytes} bytes)",
                )

            filename = derive_filename(image_url, content_type, index)
            saved_path = await self.storage.save_bytes(filename, data)
            return saved_path, None

    async def scrape_page(self, page_url: str) -> ScrapeResult:
        """Fetch `page_url`, extract `<img>` URLs, and concurrently download valid images."""
        owns_client = self._injected_client is None
        client = self._injected_client or httpx.AsyncClient(
            timeout=self.settings.request_timeout_seconds,
            follow_redirects=True,
            headers={"User-Agent": self.settings.user_agent},
        )

        try:
            try:
                page_response = await client.get(page_url)
                page_response.raise_for_status()
            except httpx.HTTPError as exc:
                raise WebpageFetchError(f"Error fetching webpage: {exc}") from exc

            img_urls = extract_image_urls(
                page_response.text,
                str(page_response.url),
                max_images=self.settings.max_images_per_scrape,
            )
            if not img_urls:
                return ScrapeResult(source_url=page_url, total_found=0)

            semaphore = asyncio.Semaphore(self.settings.max_concurrent_downloads)
            tasks = [
                self._download_single(client, semaphore, img_url, idx)
                for idx, img_url in enumerate(img_urls, start=1)
            ]
            outcomes = await asyncio.gather(*tasks)

            saved_paths: list[Path] = []
            failed: list[FailedDownload] = []
            for saved_path, failure in outcomes:
                if saved_path is not None:
                    saved_paths.append(saved_path)
                elif failure is not None:
                    failed.append(failure)

            return ScrapeResult(
                source_url=page_url,
                total_found=len(img_urls),
                saved_paths=saved_paths,
                failed=failed,
            )
        finally:
            if owns_client:
                await client.aclose()
