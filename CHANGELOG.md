# Changelog

All notable changes to **Image Scraping System Server** are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0] - 2026-11-22

### Added
- **Unified REST API (`/api/v1/images`)**:
  - `POST /api/v1/images/scrape` — Async webpage scraping with concurrent downloads and detailed saved/failed reporting.
  - `GET /api/v1/images` — List all stored images with optional `?query=` substring filter.
  - `GET /api/v1/images/search` — Dedicated case-insensitive filename search endpoint.
  - `GET /api/v1/images/{filename}` — Safe image streaming endpoint.
  - `DELETE /api/v1/images/{filename}` — Delete stored image assets by filename.
  - `GET /health` — Health check returning version, active storage directory, and stored image count.
- **Built-in Interactive Developer Experience (`app/routers/docs_ui.py`)**:
  - `GET /playground` — Zero-dependency visual API playground with live thumbnail gallery, one-click scrape/search/delete, and HTTP status/latency/JSON inspector.
  - `GET /scalar` — Modern Scalar interactive OpenAPI reference with auto-generated `curl`, Python, and JavaScript snippets.
  - Enriched Swagger UI (`/docs`) and ReDoc (`/redoc`) with `openapi_tags` and full error response documentation (`400`, `404`, `422`, `502`).
- **Centralized Configuration & Serverless Support (`app/config.py`, `.env.example`)**:
  - Immutable `Settings` loaded from environment variables (`SCRAPED_IMAGES_DIR`, `BASE_URL`, `REQUEST_TIMEOUT_SECONDS`, `MAX_CONCURRENT_DOWNLOADS`, `MAX_IMAGE_SIZE_BYTES`, `MAX_IMAGES_PER_SCRAPE`, `CORS_ORIGINS`, `SCRAPER_USER_AGENT`).
  - Automatic `/tmp/scraped_images` fallback on Vercel serverless environments (`VERCEL` env var).
  - Dynamic image URL generation derived from `Request.base_url` when `BASE_URL` is unset (eliminates hardcoded `http://localhost:8000`).
- **Automated Test Suite & CI**:
  - 12 unit and end-to-end API tests under `tests/` (`test_storage.py`, `test_scraper.py`, `test_api.py`).
  - GitHub Actions workflow (`.github/workflows/ci.yml`) running tests and repository hygiene checks on push/PR.
- **4-Tier Senior Repository Documentation**:
  - Tier 1: `README.md`, `CONTRIBUTING.md`, `SECURITY.md`, `LICENSE`, `CHANGELOG.md`, `docs/git-standards.md`.
  - Tier 2: `docs/architecture/` (`system-design.md`, `api-specification.md`, `data-model.md`, `security-and-rbac.md`) with Mermaid diagrams.
  - Tier 3: `docs/adr/` (`ADR-000` template, `ADR-001` service consolidation, `ADR-002` async HTTP & storage abstraction).
  - Tier 4: `docs/runbooks/` (`deployment-verification.md`, `incident-response.md`) and `docs/guides/api-walkthrough.md`.
  - GitHub PR and Issue templates under `.github/`.

### Changed
- **Consolidated Services**: Merged legacy `scraper_server/` and `image_search_server/` into a single modular FastAPI application under `app/` with root `main.py` entrypoint (see [ADR-001](./docs/adr/ADR-001-consolidate-scraper-and-image-search-services.md)).
- **Non-Blocking Async Scraping**: Replaced blocking `requests.get()` and sequential downloads with `httpx.AsyncClient`, `aiofiles`, and bounded `asyncio.Semaphore` concurrency (see [ADR-002](./docs/adr/ADR-002-async-http-scraping-and-storage-abstraction.md)).
- **Trimmed Dependencies**: Replaced three duplicated `requirements.txt` files with a single minimal `requirements.txt`.
- **Hardened `.gitignore`**: Expanded exclusions to prevent leaking `.env*`, private keys, logs, virtualenvs, Python bytecode, and runtime `scraped_images/*`.

### Security
- **Path-Traversal Protection**: Added `ImageStorage.resolve_safe_path()` and `sanitize_filename()` to block `../`, `..\\`, null bytes, dotfiles, and symlink escapes.
- **URL & Payload Validation**: Enforced `AnyHttpUrl` (`http`/`https` only), skipped `data:` URIs, verified `Content-Type: image/*`, and enforced `MAX_IMAGE_SIZE_BYTES` and `MAX_IMAGES_PER_SCRAPE`.
- **Error Handling**: Fixed broad `except Exception` blocks that previously masked `404 Not Found` errors as `500 Internal Server Error`.

### Removed
- Deprecated duplicate `scraper_server/` and `image_search_server/` directories and obsolete `docs/scraper_server.md` and `docs/image_search_server.md`.
- Unused dependencies (`pymysql`, `sqlalchemy`, `celery[redis]`, `pillow`, `injector`, `aiocache`, `orjson`, `python-multipart`, `requests`).
