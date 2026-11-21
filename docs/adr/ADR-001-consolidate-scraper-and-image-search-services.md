# ADR-001: Consolidate `scraper_server` and `image_search_server` into a Unified FastAPI Service

- **Status:** Accepted
- **Date:** 2026-11-22
- **Author(s):** Core Engineering Team
- **Deciders:** Repository Maintainers

---

## Context

Previously, this repository contained two separate FastAPI applications (`scraper_server/main.py` and `image_search_server/main.py`) stitched together by a root `main.py` using `APIRouter.include_router(...)`.

An audit of both services revealed critical architectural and operational issues:
1. **Overlapping Responsibilities**: Both services operated on the exact same `scraped_images/` directory and both implemented duplicate image-serving endpoints (`/scraper/images/{filename}` and `/image-search/scraper/images/{image_name}`).
2. **Broken Sub-App Mounting**: `scraper_server` mounted `StaticFiles` on its local `FastAPI()` instance, which is silently dropped when only `.router` is included into a parent FastAPI app.
3. **Divergent Configuration**: `scraper_server` resolved storage via `Path(__file__).parent.parent / "scraped_images"` and hardcoded `http://localhost:8000`, whereas `image_search_server` used `SCRAPED_IMAGES_DIR` and `BASE_URL` environment variables.
4. **Duplicated & Bloated Dependencies**: Three separate `requirements.txt` files existed, pulling in unused libraries (`pymysql`, `sqlalchemy`, `celery[redis]`, `pillow`, `injector`, `aiocache`, `orjson`).
5. **Security & Error-Handling Bugs**: Both image-serving endpoints were vulnerable to path traversal (`SCRAPED_IMAGES_DIR / filename`), and broad `except Exception` handlers swallowed `HTTPException(404)` into `500 Internal Server Error`.

---

## Decision

We will **consolidate `scraper_server` and `image_search_server` into a single, modular FastAPI application** under `app/` with a root `main.py` entrypoint:
- `app/config.py`: Single source of truth for environment-driven settings.
- `app/schemas.py`: Shared Pydantic v2 request/response contracts.
- `app/services/storage.py`: Unified, path-traversal-safe storage service.
- `app/services/scraper.py`: Async scraping and concurrent image download service.
- `app/routers/images.py`: Cohesive REST API under `/api/v1/images` covering scrape, list, search, serve, and delete.
- `app/routers/health.py`: Root discovery (`/`) and health telemetry (`/health`).

Both legacy `scraper_server/` and `image_search_server/` directories and their duplicate `requirements.txt` files are removed.

---

## Consequences

### Positive Impacts
- Eliminates duplicate code, conflicting storage paths, and triple dependency maintenance.
- Enables dynamic URL generation from the incoming request (or optional `BASE_URL`), removing hardcoded `localhost:8000` links.
- Establishes clean dependency injection (`create_app(settings=...)`) for fast, isolated unit and API testing.
- Reduces deployment package size and cold-start latency on Vercel by removing unused dependencies.

### Negative Impacts
- Clients targeting legacy unversioned paths (`/scraper/scrape-images/`, `/image-search/search-images/`) must migrate to `/api/v1/images/*`.

### Risks & Mitigations
- **Risk**: Existing consumers expecting old route paths experience 404s.
- **Mitigation**: Document the new `/api/v1/images/*` contract clearly in `README.md` and `docs/architecture/api-specification.md`.

---

## Alternatives Considered

1. **Keep two separate microservices**: Rejected because both services share a single local directory and domain model, making two services pure operational overhead with no independent scaling benefit.
2. **Deprecate `image_search_server` without preserving search**: Rejected because filename search is a core user capability that belongs naturally as `GET /api/v1/images/search` (and `GET /api/v1/images?query=...`) in the unified service.
