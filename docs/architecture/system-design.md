# System Design & Component Topology

*Status*: Living Architecture Specification  
*Version*: 2.0.0

---

## 1. System Overview

The **Image Scraping System Server** is a single, unified FastAPI service responsible for:
1. Fetching public webpages and extracting `<img>` asset URLs asynchronously.
2. Downloading valid image payloads concurrently with bounded concurrency and size limits.
3. Persisting images to a sandboxed local storage directory with strict filename sanitization.
4. Listing, searching (case-insensitive substring match), serving, and deleting stored images over RESTful HTTP endpoints.

---

## 2. Component Topology

```mermaid
flowchart TB
    subgraph External ["External Actors"]
        Client["HTTP Client (Browser / Frontend / cURL)"]
        Upstream["Target Webpage & Image CDNs"]
    end

    subgraph Runtime ["FastAPI ASGI Process (main.py)"]
        CORS["CORS Middleware"]
        HealthRouter["app/routers/health.py\nGET /, GET /health"]
        ImagesRouter["app/routers/images.py\n/api/v1/images/*"]
        DocsUIRouter["app/routers/docs_ui.py\nGET /playground, GET /scalar"]
        Config["app/config.py\nSettings (env-driven)"]
        ScraperSvc["app/services/scraper.py\nImageScraperService"]
        StorageSvc["app/services/storage.py\nImageStorage"]
    end

    subgraph Persistence ["Storage Layer"]
        FS[("Local Filesystem\nscraped_images/ or /tmp/scraped_images")]
    end

    Client --> CORS
    CORS --> HealthRouter
    CORS --> ImagesRouter
    CORS --> DocsUIRouter
    HealthRouter --> Config
    HealthRouter --> StorageSvc
    ImagesRouter --> Config
    ImagesRouter --> ScraperSvc
    ImagesRouter --> StorageSvc
    DocsUIRouter --> Config
    ScraperSvc -->|"Async HTTPX (bounded semaphore)"| Upstream
    ScraperSvc --> StorageSvc
    StorageSvc -->|"aiofiles + Path Traversal Guard"| FS
```

---

## 3. Core Request Flows

### 3.1 Webpage Image Scraping (`POST /api/v1/images/scrape`)

```mermaid
sequenceDiagram
    actor Client
    participant Router as images.py
    participant Scraper as ImageScraperService
    participant Web as Target Webpage / CDN
    participant Storage as ImageStorage

    Client->>Router: POST /api/v1/images/scrape {"url": "https://..."}
    Router->>Router: Pydantic AnyHttpUrl validation
    Router->>Scraper: scrape_page(url)
    Scraper->>Web: Async GET page_url (httpx)
    alt Upstream fetch fails
        Web-->>Scraper: HTTP error / timeout
        Scraper-->>Router: raise WebpageFetchError
        Router-->>Client: 400 Bad Request
    end
    Web-->>Scraper: 200 HTML
    Scraper->>Scraper: BeautifulSoup4 extract_image_urls (dedup, resolve relative, cap max_images)
    alt No images found
        Scraper-->>Router: ScrapeResult(total_found=0)
        Router-->>Client: 404 Not Found
    end
    loop Concurrent (Semaphore <= MAX_CONCURRENT_DOWNLOADS)
        Scraper->>Web: Async GET image_url
        Web-->>Scraper: 200 image/* bytes
        Scraper->>Scraper: Validate status, Content-Type, max_image_size_bytes
        Scraper->>Storage: save_bytes(sanitized_filename, bytes)
        Storage-->>Scraper: saved Path
    end
    Scraper-->>Router: ScrapeResult(saved_paths, failed)
    alt 0 images saved
        Router-->>Client: 502 Bad Gateway
    else >= 1 image saved
        Router-->>Client: 200 OK ScrapeResponse (saved_images + failed_images)
    end
```

### 3.2 Image Search & Retrieval (`GET /api/v1/images/search` & `GET /api/v1/images/{filename}`)

```mermaid
sequenceDiagram
    actor Client
    participant Router as images.py
    participant Storage as ImageStorage

    Client->>Router: GET /api/v1/images/search?query=logo
    Router->>Storage: list_images(query="logo")
    Storage-->>Router: [Path(".../logo.png")]
    Router-->>Client: 200 OK {"query": "logo", "count": 1, "matching_images": [...]}

    Client->>Router: GET /api/v1/images/logo.png
    Router->>Storage: get_image_path("logo.png")
    Storage->>Storage: resolve_safe_path() checks parent == base_dir
    alt Traversal / invalid name
        Storage-->>Router: raise InvalidFilenameError
        Router-->>Client: 400 Bad Request
    else File missing
        Storage-->>Router: None
        Router-->>Client: 404 Not Found
    else File exists
        Storage-->>Router: Path(".../logo.png")
        Router-->>Client: 200 OK FileResponse (binary image stream)
    end
```

---

## 4. Concurrency & Deployment Architecture

- **Non-Blocking I/O**: All webpage fetches, image downloads, and file writes use `httpx.AsyncClient` and `aiofiles`—eliminating the blocking `requests.get()` bottleneck present in the legacy `scraper_server`.
- **Bounded Concurrency**: Downloads are throttled with `asyncio.Semaphore(MAX_CONCURRENT_DOWNLOADS)` (default `10`) to avoid exhausting sockets or triggering upstream rate limits.
- **Serverless Compatibility (Vercel)**:
  - `main.py` exports `app` directly for `@vercel/python` ASGI execution, plus an optional `handler = Mangum(app)` for AWS Lambda adapters.
  - When `VERCEL` is set in the environment and `SCRAPED_IMAGES_DIR` is unset, `app/config.py` automatically targets `/tmp/scraped_images` because the Vercel deployment bundle filesystem is read-only.
  - **Note on Ephemeral Storage**: Serverless `/tmp` storage is ephemeral across cold starts. For durable multi-instance production deployments, implement an S3/R2/GCS storage adapter behind the `ImageStorage` interface (see [ADR-002](../adr/ADR-002-async-http-scraping-and-storage-abstraction.md)).
