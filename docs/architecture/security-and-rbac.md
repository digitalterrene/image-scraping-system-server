# Security Architecture & Hardening

*Status*: Living Architecture Specification  
*Version*: 2.0.0

---

## 1. Threat Model & Defenses

Because this service fetches arbitrary user-supplied URLs and writes/serves files from disk, it enforces defense-in-depth controls at every layer:

| Threat Vector | Control Implemented | Location |
|---|---|---|
| **Path Traversal (`../`, `..\\`, null bytes, dotfiles)** | `resolve_safe_path()` rejects path separators, null bytes, leading dots, and verifies `candidate.parent == base_dir.resolve()` | [`app/services/storage.py`](../../app/services/storage.py) |
| **Non-HTTP URL Schemes (`file://`, `ftp://`, `javascript:`)** | Pydantic `AnyHttpUrl` validation on `ScrapeRequest.url`; `extract_image_urls()` restricts discovered URLs to `http`/`https` | [`app/schemas.py`](../../app/schemas.py), [`app/services/scraper.py`](../../app/services/scraper.py) |
| **Non-Image Payload Injection (HTML/JS/EXE disguised as image)** | Strict `Content-Type` header verification requiring `image/*` prefix before writing bytes | [`app/services/scraper.py`](../../app/services/scraper.py) |
| **Disk / Memory Exhaustion (Zip-bomb / huge files / massive pages)** | Bounded `MAX_IMAGE_SIZE_BYTES` (default 10 MiB), `MAX_IMAGES_PER_SCRAPE` (default 50), `MAX_CONCURRENT_DOWNLOADS` (default 10), and `REQUEST_TIMEOUT_SECONDS` (default 15s) | [`app/config.py`](../../app/config.py), [`app/services/scraper.py`](../../app/services/scraper.py) |
| **Credential & Artifact Leaks in VCS** | Hardened `.gitignore` blocking `.env*`, private keys (`*.pem`, `*.key`), logs, virtualenvs, and runtime `scraped_images/*` | [`.gitignore`](../../.gitignore) |

---

## 2. Production Hardening Recommendations

When deploying this service to a public internet-facing environment:

1. **Restrict `CORS_ORIGINS`**: Override the default `*` with explicit trusted frontend origins (e.g., `CORS_ORIGINS=https://app.example.com`).
2. **SSRF Protection**: If running inside a private VPC or cloud environment with internal metadata endpoints (e.g., `169.254.169.254`, `127.0.0.1`, RFC 1918 subnets), add DNS resolution + private IP range blocking or route outbound egress through an isolated egress proxy.
3. **Authentication & Rate Limiting**: Front the API with an API gateway, Vercel Firewall, or reverse proxy (Nginx/Cloudflare) enforcing API key / JWT authentication and per-IP rate limits on `POST /api/v1/images/scrape`.
4. **Content-Disposition & CSP Headers**: When serving untrusted SVG files (`image/svg+xml`), ensure downstream proxies apply `Content-Security-Policy: sandbox` or disallow SVG scraping if untrusted users view raw image URLs directly in the same origin.
