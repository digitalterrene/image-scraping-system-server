"""End-to-end API tests for the unified FastAPI application."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

from app.config import Settings
from app.routers.images import get_scraper_service
from app.services.scraper import FailedDownload, ScrapeResult
from main import create_app


class _FakeScraperService:
    def __init__(self, storage_dir: Path) -> None:
        self.storage_dir = storage_dir

    async def scrape_page(self, page_url: str) -> ScrapeResult:
        if "empty" in page_url:
            return ScrapeResult(source_url=page_url, total_found=0)

        saved_path = self.storage_dir / "hero_banner.png"
        saved_path.write_bytes(b"\x89PNG\r\n\x1a\nFAKE")
        return ScrapeResult(
            source_url=page_url,
            total_found=2,
            saved_paths=[saved_path],
            failed=[FailedDownload(source_url="https://example.com/broken.png", reason="Non-200 status code (404)")],
        )


class TestAPI(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.storage_dir = Path(self._tmp.name)
        self.settings = Settings(scraped_images_dir=self.storage_dir)
        self.app = create_app(settings=self.settings)
        self.app.dependency_overrides[get_scraper_service] = lambda: _FakeScraperService(self.storage_dir)
        self.client = TestClient(self.app)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def test_root_and_health(self) -> None:
        root_resp = self.client.get("/")
        self.assertEqual(root_resp.status_code, 200)
        self.assertEqual(root_resp.json()["status"], "running")

        health_resp = self.client.get("/health")
        self.assertEqual(health_resp.status_code, 200)
        body = health_resp.json()
        self.assertEqual(body["status"], "healthy")
        self.assertEqual(body["stored_images_count"], 0)

    def test_scrape_list_search_serve_and_delete_flow(self) -> None:
        # 1. Scrape images
        scrape_resp = self.client.post(
            "/api/v1/images/scrape",
            json={"url": "https://example.com/gallery"},
        )
        self.assertEqual(scrape_resp.status_code, 200)
        scrape_data = scrape_resp.json()
        self.assertEqual(scrape_data["saved_count"], 1)
        self.assertEqual(scrape_data["failed_count"], 1)
        self.assertEqual(scrape_data["saved_images"][0]["filename"], "hero_banner.png")

        # 2. List all images
        list_resp = self.client.get("/api/v1/images")
        self.assertEqual(list_resp.status_code, 200)
        self.assertEqual(list_resp.json()["count"], 1)

        # 3. Search images
        search_resp = self.client.get("/api/v1/images/search", params={"query": "hero"})
        self.assertEqual(search_resp.status_code, 200)
        self.assertEqual(search_resp.json()["count"], 1)

        no_match = self.client.get("/api/v1/images/search", params={"query": "nonexistent"})
        self.assertEqual(no_match.status_code, 404)

        # 4. Serve image
        img_resp = self.client.get("/api/v1/images/hero_banner.png")
        self.assertEqual(img_resp.status_code, 200)
        self.assertTrue(img_resp.content.startswith(b"\x89PNG"))

        # 5. Reject invalid hidden filename
        bad_resp = self.client.get("/api/v1/images/.env")
        self.assertEqual(bad_resp.status_code, 400)

        # 6. Delete image
        del_resp = self.client.delete("/api/v1/images/hero_banner.png")
        self.assertEqual(del_resp.status_code, 200)
        self.assertEqual(self.client.get("/api/v1/images/hero_banner.png").status_code, 404)

    def test_scrape_rejects_invalid_url_scheme(self) -> None:
        resp = self.client.post("/api/v1/images/scrape", json={"url": "file:///etc/passwd"})
        self.assertEqual(resp.status_code, 422)

    def test_scrape_returns_404_when_no_images_found(self) -> None:
        resp = self.client.post("/api/v1/images/scrape", json={"url": "https://example.com/empty"})
        self.assertEqual(resp.status_code, 404)

    def test_interactive_docs_and_playground_endpoints(self) -> None:
        for path in ["/playground", "/scalar", "/docs", "/redoc", "/openapi.json"]:
            resp = self.client.get(path)
            self.assertEqual(resp.status_code, 200, msg=f"Expected 200 for {path}")


if __name__ == "__main__":
    unittest.main()
