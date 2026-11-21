# API Specification

*Status*: Living Specification  
*Base Path*: `/api/v1` (plus root discovery `/` and `/health`)

---

## 1. Health & Discovery

### `GET /`
Returns service metadata, version, documentation link, and available endpoints.

**Example Response (`200 OK`):**
```json
{
  "service": "Image Scraping System Server",
  "version": "2.0.0",
  "status": "running",
  "interactive_docs": {
    "playground": "http://127.0.0.1:8000/playground",
    "swagger_ui": "http://127.0.0.1:8000/docs",
    "scalar": "http://127.0.0.1:8000/scalar",
    "redoc": "http://127.0.0.1:8000/redoc",
    "openapi_json": "http://127.0.0.1:8000/openapi.json"
  },
  "endpoints": {
    "health": "/health",
    "scrape": "/api/v1/images/scrape",
    "list_images": "/api/v1/images",
    "search_images": "/api/v1/images/search",
    "get_image": "/api/v1/images/{filename}",
    "delete_image": "/api/v1/images/{filename}"
  }
}
```

### `GET /health`
Reports service health and storage telemetry.

**Example Response (`200 OK`):**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "storage_dir": "/app/scraped_images",
  "stored_images_count": 4
}
```

---

## 2. Image Operations

### `POST /api/v1/images/scrape`
Fetches a public HTTP/HTTPS webpage, extracts unique `<img>` URLs (`src` and `data-src`), concurrently downloads valid `image/*` payloads, and saves them to storage.

**Request Body:**
```json
{
  "url": "https://example.com/gallery"
}
```

**Example Response (`200 OK`):**
```json
{
  "message": "Images scraped and saved successfully.",
  "source_url": "https://example.com/gallery",
  "total_found": 2,
  "saved_count": 1,
  "failed_count": 1,
  "saved_images": [
    {
      "filename": "hero_banner.png",
      "url": "http://127.0.0.1:8000/api/v1/images/hero_banner.png",
      "size_bytes": 48291
    }
  ],
  "failed_images": [
    {
      "source_url": "https://example.com/broken.png",
      "reason": "Non-200 status code (404)"
    }
  ]
}
```

**Error Codes:**
| Status | Cause |
|---|---|
| `400 Bad Request` | Upstream webpage could not be fetched (network error, timeout, or non-2xx response) |
| `404 Not Found` | Webpage loaded, but no valid `<img>` URLs were discovered |
| `422 Unprocessable Entity` | Request body failed Pydantic validation (e.g., non-HTTP/HTTPS URL scheme) |
| `502 Bad Gateway` | Images were discovered on the page, but every download failed validation |

---

### `GET /api/v1/images`
Lists all stored images, sorted alphabetically. Accepts an optional `query` parameter to filter filenames.

**Query Parameters:**
- `query` *(string, optional)*: Case-insensitive substring filter.

**Example Request:**
```bash
curl "http://127.0.0.1:8000/api/v1/images?query=hero"
```

**Example Response (`200 OK`):**
```json
{
  "count": 1,
  "images": [
    {
      "filename": "hero_banner.png",
      "url": "http://127.0.0.1:8000/api/v1/images/hero_banner.png",
      "size_bytes": 48291
    }
  ]
}
```

---

### `GET /api/v1/images/search`
Dedicated search endpoint for matching stored images by filename substring. Returns `404 Not Found` when no images match.

**Query Parameters:**
- `query` *(string, required)*: Non-empty case-insensitive substring.

**Example Request:**
```bash
curl "http://127.0.0.1:8000/api/v1/images/search?query=hero"
```

**Example Response (`200 OK`):**
```json
{
  "query": "hero",
  "count": 1,
  "matching_images": [
    {
      "filename": "hero_banner.png",
      "url": "http://127.0.0.1:8000/api/v1/images/hero_banner.png",
      "size_bytes": 48291
    }
  ]
}
```

**Error Codes:**
- `400 Bad Request`: `query` contains only whitespace.
- `404 Not Found`: No stored images match `query`.

---

### `GET /api/v1/images/{filename}`
Streams a stored image file with its detected MIME type.

**Example Request:**
```bash
curl -O "http://127.0.0.1:8000/api/v1/images/hero_banner.png"
```

**Error Codes:**
- `400 Bad Request`: Invalid filename or path-traversal attempt.
- `404 Not Found`: Image does not exist in storage.

---

### `DELETE /api/v1/images/{filename}`
Deletes a stored image from disk.

**Example Response (`200 OK`):**
```json
{
  "message": "Image deleted successfully.",
  "filename": "hero_banner.png"
}
```

**Error Codes:**
- `400 Bad Request`: Invalid filename or path-traversal attempt.
- `404 Not Found`: Image does not exist in storage.

---

## 3. Interactive Developer Documentation & Playground

These HTML routes are served directly by FastAPI (excluded from the OpenAPI schema) so developers can explore and test endpoints without Postman or Thunder Client:

| Method | Path | Description |
|---|---|---|
| `GET` | `/playground` | Self-contained visual API playground with live JSON inspector and scraped image thumbnail gallery |
| `GET` | `/scalar` | Scalar interactive OpenAPI reference with live request execution and multi-language code snippets |
| `GET` | `/docs` | Swagger UI interactive explorer |
| `GET` | `/redoc` | ReDoc schema & endpoint reference |
| `GET` | `/openapi.json` | Raw OpenAPI 3.1 JSON specification |
