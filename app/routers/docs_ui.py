"""Interactive developer documentation and zero-dependency API playground routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from fastapi.responses import HTMLResponse

from app.config import Settings, get_settings

router = APIRouter(tags=["Interactive Docs"], include_in_schema=False)


@router.get("/scalar", response_class=HTMLResponse)
async def scalar_api_reference(settings: Settings = Depends(get_settings)) -> HTMLResponse:
    """Serve the modern Scalar interactive OpenAPI reference and request tester."""
    html = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>{settings.app_name} — Scalar API Reference</title>
  </head>
  <body>
    <script
      id="api-reference"
      data-url="/openapi.json"
      data-configuration='{{"theme":"purple","layout":"modern"}}'
    ></script>
    <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
  </body>
</html>
"""
    return HTMLResponse(content=html)


@router.get("/playground", response_class=HTMLResponse)
async def api_playground(settings: Settings = Depends(get_settings)) -> HTMLResponse:
    """Serve a self-contained visual API playground to test all endpoints in the browser."""
    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{settings.app_name} — API Playground</title>
  <style>
    :root {{
      --bg: #0f172a;
      --panel: #1e293b;
      --border: #334155;
      --text: #f8fafc;
      --muted: #94a3b8;
      --accent: #38bdf8;
      --accent-hover: #0ea5e9;
      --danger: #ef4444;
      --success: #22c55e;
      --code-bg: #020617;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
      line-height: 1.5;
    }}
    header {{
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: space-between;
      gap: 1rem;
      padding: 1rem 1.5rem;
      border-bottom: 1px solid var(--border);
      background: rgba(15, 23, 42, 0.9);
      position: sticky;
      top: 0;
      z-index: 10;
    }}
    header h1 {{ margin: 0; font-size: 1.15rem; }}
    .nav-links {{ display: flex; gap: 0.75rem; flex-wrap: wrap; }}
    .nav-links a {{
      color: var(--accent);
      text-decoration: none;
      font-size: 0.875rem;
      padding: 0.35rem 0.65rem;
      border: 1px solid var(--border);
      border-radius: 6px;
    }}
    .nav-links a:hover {{ border-color: var(--accent); }}
    main {{
      max-width: 1120px;
      margin: 0 auto;
      padding: 1.5rem;
      display: grid;
      gap: 1.25rem;
    }}
    .grid-2 {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
      gap: 1.25rem;
    }}
    .card {{
      background: var(--panel);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 1.25rem;
    }}
    .card h2 {{
      margin: 0 0 0.35rem;
      font-size: 1rem;
      display: flex;
      align-items: center;
      gap: 0.5rem;
    }}
    .card p {{ margin: 0 0 0.9rem; color: var(--muted); font-size: 0.875rem; }}
    .badge {{
      font-size: 0.7rem;
      font-weight: 700;
      padding: 0.15rem 0.45rem;
      border-radius: 4px;
      text-transform: uppercase;
    }}
    .get {{ background: #0369a1; color: #e0f2fe; }}
    .post {{ background: #15803d; color: #dcfce7; }}
    .delete {{ background: #b91c1c; color: #fee2e2; }}
    .row {{ display: flex; gap: 0.5rem; flex-wrap: wrap; }}
    input[type="text"], input[type="url"] {{
      flex: 1;
      min-width: 180px;
      padding: 0.55rem 0.75rem;
      border-radius: 6px;
      border: 1px solid var(--border);
      background: var(--code-bg);
      color: var(--text);
      font-size: 0.9rem;
    }}
    button {{
      padding: 0.55rem 0.95rem;
      border-radius: 6px;
      border: none;
      background: var(--accent);
      color: #082f49;
      font-weight: 600;
      cursor: pointer;
      font-size: 0.875rem;
    }}
    button:hover {{ background: var(--accent-hover); }}
    button.secondary {{
      background: transparent;
      color: var(--text);
      border: 1px solid var(--border);
    }}
    button.danger {{
      background: var(--danger);
      color: white;
      padding: 0.35rem 0.65rem;
      font-size: 0.78rem;
    }}
    pre {{
      background: var(--code-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 0.9rem;
      overflow-x: auto;
      font-size: 0.82rem;
      margin: 0.75rem 0 0;
      max-height: 300px;
    }}
    .meta {{
      display: flex;
      gap: 1rem;
      font-size: 0.82rem;
      color: var(--muted);
      margin-top: 0.5rem;
    }}
    .gallery {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
      gap: 1rem;
      margin-top: 1rem;
    }}
    .thumb {{
      background: var(--code-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      overflow: hidden;
      display: flex;
      flex-direction: column;
    }}
    .thumb img {{
      width: 100%;
      height: 130px;
      object-fit: cover;
      background: #0b1120;
    }}
    .thumb-body {{
      padding: 0.6rem;
      display: flex;
      flex-direction: column;
      gap: 0.4rem;
    }}
    .thumb-name {{
      font-size: 0.78rem;
      word-break: break-all;
      color: var(--text);
    }}
    .thumb-actions {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 0.4rem;
    }}
    .thumb-actions a {{
      color: var(--accent);
      font-size: 0.78rem;
      text-decoration: none;
    }}
  </style>
</head>
<body>
  <header>
    <h1>{settings.app_name} <span style="color:var(--muted);font-weight:400;">v{settings.app_version} — Playground</span></h1>
    <nav class="nav-links">
      <a href="/docs" target="_blank">Swagger UI (/docs)</a>
      <a href="/scalar" target="_blank">Scalar Docs (/scalar)</a>
      <a href="/redoc" target="_blank">ReDoc (/redoc)</a>
      <a href="/openapi.json" target="_blank">OpenAPI JSON</a>
    </nav>
  </header>

  <main>
    <div class="grid-2">
      <section class="card">
        <h2><span class="badge post">POST</span> /api/v1/images/scrape</h2>
        <p>Scrape all valid <code>&lt;img&gt;</code> assets from a public webpage URL.</p>
        <div class="row">
          <input id="scrapeUrl" type="url" placeholder="https://example.com" value="https://httpbin.org/html" />
          <button onclick="runScrape()">Scrape</button>
        </div>
      </section>

      <section class="card">
        <h2><span class="badge get">GET</span> /api/v1/images/search</h2>
        <p>Search stored images by filename substring, or list everything in storage.</p>
        <div class="row">
          <input id="searchQuery" type="text" placeholder="e.g. logo, png, hero" />
          <button onclick="runSearch()">Search</button>
          <button class="secondary" onclick="loadImages()">List All</button>
          <button class="secondary" onclick="runHealth()">Health</button>
        </div>
      </section>
    </div>

    <section class="card">
      <h2>Live Response Inspector</h2>
      <div class="meta" id="responseMeta">Ready — run any request above to inspect the live response.</div>
      <pre id="responseBody">{{}}</pre>
    </section>

    <section class="card">
      <h2>Stored Images Gallery <span id="galleryCount" style="color:var(--muted);font-size:0.85rem;font-weight:400;"></span></h2>
      <p>Click <strong>Open</strong> to test <code>GET /api/v1/images/{{filename}}</code> or <strong>Delete</strong> to test <code>DELETE /api/v1/images/{{filename}}</code>.</p>
      <div class="gallery" id="gallery"></div>
    </section>
  </main>

  <script>
    async function callApi(method, path, body = null) {{
      const started = performance.now();
      const opts = {{ method, headers: {{}} }};
      if (body !== null) {{
        opts.headers["Content-Type"] = "application/json";
        opts.body = JSON.stringify(body);
      }}
      const res = await fetch(path, opts);
      const elapsed = Math.round(performance.now() - started);
      let data;
      try {{
        data = await res.json();
      }} catch {{
        data = {{ raw: await res.text() }};
      }}
      document.getElementById("responseMeta").textContent =
        `${{method}} ${{path}}  •  HTTP ${{res.status}} ${{res.statusText}}  •  ${{elapsed}} ms`;
      document.getElementById("responseBody").textContent = JSON.stringify(data, null, 2);
      return {{ res, data }};
    }}

    function renderGallery(images) {{
      const gallery = document.getElementById("gallery");
      const countEl = document.getElementById("galleryCount");
      countEl.textContent = `(${{images.length}} shown)`;
      if (!images.length) {{
        gallery.innerHTML = '<div style="color:var(--muted);font-size:0.875rem;">No images to display yet. Try scraping a page above.</div>';
        return;
      }}
      gallery.innerHTML = images.map(img => `
        <div class="thumb">
          <img src="${{img.url}}" alt="${{img.filename}}" loading="lazy" />
          <div class="thumb-body">
            <div class="thumb-name">${{img.filename}}</div>
            <div style="color:var(--muted);font-size:0.75rem;">${{(img.size_bytes / 1024).toFixed(1)}} KB</div>
            <div class="thumb-actions">
              <a href="${{img.url}}" target="_blank">Open</a>
              <button class="danger" onclick="deleteImage('${{encodeURIComponent(img.filename)}}')">Delete</button>
            </div>
          </div>
        </div>
      `).join("");
    }}

    async function runHealth() {{
      await callApi("GET", "/health");
    }}

    async function loadImages() {{
      const {{ res, data }} = await callApi("GET", "/api/v1/images");
      if (res.ok) renderGallery(data.images || []);
    }}

    async function runSearch() {{
      const q = document.getElementById("searchQuery").value.trim();
      if (!q) return loadImages();
      const {{ res, data }} = await callApi("GET", `/api/v1/images/search?query=${{encodeURIComponent(q)}}`);
      renderGallery(res.ok ? (data.matching_images || []) : []);
    }}

    async function runScrape() {{
      const url = document.getElementById("scrapeUrl").value.trim();
      if (!url) return;
      const {{ res }} = await callApi("POST", "/api/v1/images/scrape", {{ url }});
      if (res.ok) await loadImages();
    }}

    async function deleteImage(encodedFilename) {{
      const {{ res }} = await callApi("DELETE", `/api/v1/images/${{encodedFilename}}`);
      if (res.ok) await loadImages();
    }}

    // Load current stored images on page open
    loadImages();
  </script>
</body>
</html>
"""
    return HTMLResponse(content=html)
