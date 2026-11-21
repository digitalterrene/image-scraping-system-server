# API Walkthrough & Interactive Testing Guide

This guide walks you through every endpoint of **Image Scraping System Server**—both visually in your browser (without Postman or Thunder Client) and programmatically via `curl`, PowerShell, Python, or JavaScript.

---

## 1. Start the Server

```powershell
python -m uvicorn main:app --reload
```

Once running on `http://127.0.0.1:8000`, you immediately have **four built-in browser tools**—no external REST client required:

| Tool | URL | Best For |
|---|---|---|
| **Visual API Playground** | `http://127.0.0.1:8000/playground` | Scraping URLs, previewing scraped image thumbnails, searching, deleting, and inspecting live JSON responses + latency |
| **Scalar API Reference** | `http://127.0.0.1:8000/scalar` | Modern Postman-like interactive API tester with auto-generated code snippets (`curl`, Python, JS, Go, etc.) |
| **Swagger UI** | `http://127.0.0.1:8000/docs` | Standard OpenAPI **"Try it out" -> "Execute"** endpoint testing |
| **ReDoc** | `http://127.0.0.1:8000/redoc` | Clean, readable reference documentation for schemas and responses |

---

## 2. End-to-End Walkthrough

Follow these 6 steps in order to exercise the entire lifecycle of the API.

### Step 1: Check Service Health (`GET /health`)
Verify the server is running and inspect where images are being stored.

- **In `/playground`**: Click **Health**.
- **PowerShell**:
  ```powershell
  Invoke-RestMethod -Uri "http://127.0.0.1:8000/health"
  ```
- **cURL**:
  ```bash
  curl http://127.0.0.1:8000/health
  ```

**Response (`200 OK`):**
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "storage_dir": "C:\\Users\\User\\DevProjects\\image-scraping-system-server\\scraped_images",
  "stored_images_count": 0
}
```

---

### Step 2: Scrape Images from a Webpage (`POST /api/v1/images/scrape`)
Provide any public `http://` or `https://` webpage URL. The server fetches the HTML asynchronously, extracts unique `<img>` URLs (`src` and `data-src`), downloads valid `image/*` assets concurrently, and returns both saved images and any individual download failures.

- **In `/playground`**: Paste a URL (for example, `https://www.python.org`) and click **Scrape**. Thumbnails appear automatically in the gallery below.
- **In `/docs` or `/scalar`**: Open `POST /api/v1/images/scrape`, click **Try it out** / **Test Request**, enter a URL, and execute.
- **PowerShell**:
  ```powershell
  Invoke-RestMethod -Method Post `
    -Uri "http://127.0.0.1:8000/api/v1/images/scrape" `
    -ContentType "application/json" `
    -Body '{"url": "https://www.python.org"}'
  ```
- **cURL**:
  ```bash
  curl -X POST "http://127.0.0.1:8000/api/v1/images/scrape" \
    -H "Content-Type: application/json" \
    -d '{"url": "https://www.python.org"}'
  ```

**Response (`200 OK`):**
```json
{
  "message": "Images scraped and saved successfully.",
  "source_url": "https://www.python.org/",
  "total_found": 2,
  "saved_count": 2,
  "failed_count": 0,
  "saved_images": [
    {
      "filename": "python-logo.png",
      "url": "http://127.0.0.1:8000/api/v1/images/python-logo.png",
      "size_bytes": 15770
    }
  ],
  "failed_images": []
}
```

---

### Step 3: List All Stored Images (`GET /api/v1/images`)
Returns every image currently in storage, sorted alphabetically. You can also pass an optional `?query=` parameter to filter inline (returns `count: 0, images: []` if nothing matches).

- **In `/playground`**: Click **List All**.
- **PowerShell**:
  ```powershell
  Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/images"
  ```
- **cURL**:
  ```bash
  curl "http://127.0.0.1:8000/api/v1/images"
  ```

---

### Step 4: Search Stored Images by Filename (`GET /api/v1/images/search`)
Performs a case-insensitive substring search across stored filenames. Returns `404 Not Found` if no files match.

- **In `/playground`**: Type `logo` in the search box and click **Search**.
- **PowerShell**:
  ```powershell
  Invoke-RestMethod -Uri "http://127.0.0.1:8000/api/v1/images/search?query=logo"
  ```
- **cURL**:
  ```bash
  curl "http://127.0.0.1:8000/api/v1/images/search?query=logo"
  ```

**Response (`200 OK`):**
```json
{
  "query": "logo",
  "count": 1,
  "matching_images": [
    {
      "filename": "python-logo.png",
      "url": "http://127.0.0.1:8000/api/v1/images/python-logo.png",
      "size_bytes": 15770
    }
  ]
}
```

---

### Step 5: Retrieve / Preview an Image (`GET /api/v1/images/{filename}`)
Streams the raw image bytes directly with the proper `Content-Type` header.

- **In `/playground`**: Click **Open** on any thumbnail card.
- **Browser**: Visit `http://127.0.0.1:8000/api/v1/images/python-logo.png`.
- **cURL (download to file)**:
  ```bash
  curl -O "http://127.0.0.1:8000/api/v1/images/python-logo.png"
  ```

---

### Step 6: Delete a Stored Image (`DELETE /api/v1/images/{filename}`)
Removes the image file from local storage.

- **In `/playground`**: Click **Delete** on any thumbnail card.
- **PowerShell**:
  ```powershell
  Invoke-RestMethod -Method Delete -Uri "http://127.0.0.1:8000/api/v1/images/python-logo.png"
  ```
- **cURL**:
  ```bash
  curl -X DELETE "http://127.0.0.1:8000/api/v1/images/python-logo.png"
  ```

**Response (`200 OK`):**
```json
{
  "message": "Image deleted successfully.",
  "filename": "python-logo.png"
}
```

---

## 3. Client Code Snippets

### Python (`httpx`)
```python
import httpx

BASE = "http://127.0.0.1:8000"

with httpx.Client(base_url=BASE, timeout=30.0) as client:
    # 1. Scrape
    scrape = client.post("/api/v1/images/scrape", json={"url": "https://www.python.org"})
    scrape.raise_for_status()
    print("Scraped:", scrape.json()["saved_count"], "images")

    # 2. Search
    found = client.get("/api/v1/images/search", params={"query": "python"})
    print("Matches:", found.json()["matching_images"])
```

### JavaScript (`fetch`)
```javascript
const BASE = "http://127.0.0.1:8000";

const res = await fetch(`${BASE}/api/v1/images/scrape`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({ url: "https://www.python.org" }),
});
const data = await res.json();
console.log(data.saved_images);
```

---

## 4. Common Status Codes & Troubleshooting

| Status | Meaning | How to Resolve |
|---|---|---|
| `400 Bad Request` | Upstream webpage failed to load, whitespace-only search query, or invalid/unsafe filename (e.g. `.env`, `../`) | Check that the target URL is reachable and filenames contain no path segments or leading dots |
| `404 Not Found` | Webpage had no `<img>` tags, search matched 0 files, or requested image does not exist | Note that JavaScript-rendered SPAs may not expose `<img>` tags in static HTML |
| `422 Unprocessable Entity` | Invalid JSON body or non-HTTP/HTTPS URL scheme (e.g. `file://`) | Ensure `url` starts with `http://` or `https://` |
| `502 Bad Gateway` | `<img>` tags were found, but every image download failed (non-200, non-`image/*` content type, or exceeded `MAX_IMAGE_SIZE_BYTES`) | Check target site hotlink protection or increase `REQUEST_TIMEOUT_SECONDS` / `MAX_IMAGE_SIZE_BYTES` |
