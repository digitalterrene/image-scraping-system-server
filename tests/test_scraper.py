"""Unit tests for HTML image extraction and asynchronous scraping."""

from __future__ import annotations

import asyncio
import tempfile
import unittest
from pathlib import Path

import httpx

from app.config import Settings
from app.services.scraper import (
    ImageScraperService,
    WebpageFetchError,
    derive_filename,
    extract_image_urls,
)
from app.services.storage import ImageStorage


class TestScraperUtilities(unittest.TestCase):
    def test_extract_image_urls_resolves_deduplicates_and_skips_data_uri(self) -> None:
        html = """
        <html>
          <body>
            <img src="/assets/logo.png" />
            <img src="https://cdn.example.com/hero.jpg" />
            <img src="/assets/logo.png" />
            <img data-src="gallery/pic.webp" />
            <img src="data:image/png;base64,AAAA" />
            <img src="javascript:alert(1)" />
          </body>
        </html>
        """
        urls = extract_image_urls(html, "https://example.com/blog/post")
        self.assertEqual(
            urls,
            [
                "https://example.com/assets/logo.png",
                "https://cdn.example.com/hero.jpg",
                "https://example.com/blog/gallery/pic.webp",
            ],
        )

    def test_derive_filename_infers_extension_from_content_type(self) -> None:
        self.assertEqual(
            derive_filename("https://example.com/media/12345", "image/webp; charset=utf-8", 1),
            "12345.webp",
        )
        self.assertEqual(
            derive_filename("https://example.com/", "image/png", 2),
            "image_2.png",
        )


class TestImageScraperService(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.settings = Settings(
            scraped_images_dir=Path(self._tmp.name),
            max_image_size_bytes=1024,
            max_concurrent_downloads=4,
        )
        self.storage = ImageStorage(self.settings.scraped_images_dir)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_scrape_page_saves_valid_images_and_tracks_failures(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            url = str(request.url)
            if url == "https://example.com/page":
                html = """
                <img src="/ok.png" />
                <img src="/not-image.txt" />
                <img src="/too-big.jpg" />
                <img src="/missing.png" />
                """
                return httpx.Response(200, text=html, headers={"content-type": "text/html"})
            if url == "https://example.com/ok.png":
                return httpx.Response(200, content=b"\x89PNGdata", headers={"content-type": "image/png"})
            if url == "https://example.com/not-image.txt":
                return httpx.Response(200, content=b"hello", headers={"content-type": "text/plain"})
            if url == "https://example.com/too-big.jpg":
                return httpx.Response(200, content=b"x" * 2048, headers={"content-type": "image/jpeg"})
            return httpx.Response(404)

        async def run_scrape():
            transport = httpx.MockTransport(handler)
            async with httpx.AsyncClient(transport=transport) as client:
                service = ImageScraperService(self.storage, self.settings, http_client=client)
                return await service.scrape_page("https://example.com/page")

        result = asyncio.run(run_scrape())
        self.assertEqual(result.total_found, 4)
        self.assertEqual(len(result.saved_paths), 1)
        self.assertEqual(result.saved_paths[0].name, "ok.png")
        self.assertEqual(len(result.failed), 3)

    def test_scrape_page_raises_webpage_fetch_error_on_upstream_failure(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(503)

        async def run_scrape():
            transport = httpx.MockTransport(handler)
            async with httpx.AsyncClient(transport=transport) as client:
                service = ImageScraperService(self.storage, self.settings, http_client=client)
                await service.scrape_page("https://example.com/down")

        with self.assertRaises(WebpageFetchError):
            asyncio.run(run_scrape())


if __name__ == "__main__":
    unittest.main()
