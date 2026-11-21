# ADR-002: Adopt Async HTTPX Scraping, Bounded Concurrency, and Encapsulated Storage

- **Status:** Accepted
- **Date:** 2026-11-22
- **Author(s):** Core Engineering Team
- **Deciders:** Repository Maintainers

---

## Context

The legacy `scraper_server` called synchronous `requests.get(url)` inside an `async def` FastAPI endpoint (blocking the ASGI event loop) and downloaded discovered images sequentially in a `for` loop. Additionally, it wrote files directly to the repository root (`scraped_images/`), which fails on read-only serverless filesystems such as Vercel.

---

## Decision

1. **Fully Asynchronous HTTP Stack**: Replace `requests` with `httpx.AsyncClient` for both webpage fetching and image downloading, configured with explicit timeouts, redirect following, and a descriptive `User-Agent`.
2. **Bounded Concurrency**: Use `asyncio.gather` guarded by `asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)` (default `10`) and enforce `MAX_IMAGES_PER_SCRAPE` (default `50`) and `MAX_IMAGE_SIZE_BYTES` (default `10 MiB`).
3. **Encapsulated Storage (`ImageStorage`)**: Isolate all filesystem reads, writes, searches, deletions, and path-traversal validation inside `app/services/storage.py`. Automatically default to `/tmp/scraped_images` when running on Vercel (`VERCEL` env var set).

---

## Consequences

### Positive Impacts
- Eliminates event-loop blocking under concurrent load.
- Significantly faster scrape latency when webpages contain multiple images.
- Protects memory, disk, and file descriptors via configurable upper bounds.
- Makes future migration to S3, Cloudflare R2, or GCS a clean adapter swap behind `ImageStorage`.

### Negative Impacts
- On serverless platforms (Vercel), `/tmp/scraped_images` is ephemeral and does not persist across cold starts or separate lambda instances.

### Risks & Mitigations
- **Risk**: Users deploying on Vercel may expect scraped images to persist indefinitely.
- **Mitigation**: Document serverless ephemeral storage behavior prominently in `docs/architecture/system-design.md` and `docs/runbooks/deployment-verification.md`.

---

## Alternatives Considered

1. **Background job queue (Celery + Redis)**: Deferred to keep deployment lightweight and zero-infrastructure. Can be added later if long-running crawl jobs are needed.
2. **Headless browser scraping (Playwright)**: Rejected for baseline v2 due to large container footprint and incompatibility with lightweight Vercel Python functions.
