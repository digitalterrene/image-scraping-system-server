# Deployment Verification Runbook

Step-by-step smoke tests and verification procedures for local, container, and Vercel releases of **Image Scraping System Server**.

---

## 1. Pre-Deployment Quality Gates

Run locally or verify in GitHub Actions (`.github/workflows/ci.yml`):

```bash
# 1. Run full unit & API test suite
python -m unittest discover -s tests -v

# 2. Run repository hygiene audit
node .agents/skills/senior-repo-standards/scripts/audit-hygiene.js
```

---

## 2. Post-Deployment Smoke Tests

Set `TARGET_URL` to your deployed base URL (e.g., `http://127.0.0.1:8000` or `https://image-scraping-system-server.vercel.app`):

```bash
# 1. Verify root service discovery (expect HTTP 200)
curl -fsS "${TARGET_URL}/"

# 2. Verify health endpoint & storage directory (expect status="healthy")
curl -fsS "${TARGET_URL}/health"

# 3. Verify OpenAPI schema loads cleanly
curl -fsS "${TARGET_URL}/openapi.json" > /dev/null && echo "OpenAPI OK"

# 4. Verify list endpoint responds cleanly
curl -fsS "${TARGET_URL}/api/v1/images"

# 5. Verify scrape validation rejects non-HTTP schemes (expect HTTP 422)
curl -s -o /dev/null -w "%{http_code}\n" -X POST "${TARGET_URL}/api/v1/images/scrape" \
  -H "Content-Type: application/json" \
  -d '{"url":"file:///etc/passwd"}'

# 6. Verify path-traversal defense (expect HTTP 400)
curl -s -o /dev/null -w "%{http_code}\n" "${TARGET_URL}/api/v1/images/.env"
```

---

## 3. Verification Checklist

- [ ] `GET /health` returns HTTP 200 with `"status": "healthy"`.
- [ ] `GET /playground` loads the visual API playground and fetches `/api/v1/images`.
- [ ] `GET /scalar` and `GET /docs` render interactive OpenAPI documentation without console errors.
- [ ] `POST /api/v1/images/scrape` succeeds against a known public page containing images.
- [ ] `GET /api/v1/images/search?query=...` returns matching URLs with the correct public host (not `localhost:8000`).
- [ ] `GET /api/v1/images/{filename}` serves binary image bytes with valid `Content-Type`.
- [ ] On Vercel, confirm `storage_dir` in `/health` resolves to `/tmp/scraped_images` (or configured writable path).

---

## 4. Rollback Procedure

- **Vercel**: Promote the previous healthy deployment in the Vercel Dashboard or run `vercel rollback`.
- **Git / Self-Hosted**: Revert the release commit (`git revert <sha>`) and redeploy the previous container/process.
