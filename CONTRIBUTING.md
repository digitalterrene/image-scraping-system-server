# Contributing to Image Scraping System Server

Thank you for contributing to **Image Scraping System Server**. Maintaining a clean, reliable, and well-documented Python backend requires consistent engineering standards.

---

## 1. Code of Conduct

We are committed to providing a welcoming, respectful, and inclusive environment for all contributors regardless of background or experience level.

---

## 2. Engineering Non-Negotiables

Before opening a Pull Request, please review our [Git Engineering Standards](./docs/git-standards.md).

**Key Rules:**
1. **Branch Naming**: Branch from `main` using `feat/<scope>-<desc>`, `fix/<scope>-<desc>`, `refactor/<scope>-<desc>`, `docs/<scope>-<desc>`, or `chore/<scope>-<desc>`.
2. **Conventional Commits**: Every commit must follow [Conventional Commits](https://www.conventionalcommits.org/) (`<type>(<scope>): <imperative summary>`).
3. **Chain-of-Thought (CoT)**: For non-trivial changes or architectural refactors, document the root cause, alternatives considered, and side effects in the commit body.
4. **Pre-Commit Verification**: All unit and API tests must pass, and no secrets, `.env` files, or `__pycache__` artifacts may be staged.

---

## 3. Local Development Workflow

1. Fork or clone the repository:
   ```bash
   git clone https://github.com/digitalterrene/image-scraping-system-server.git
   cd image-scraping-system-server
   ```
2. Create an isolated branch:
   ```bash
   git checkout -b feat/scraper-add-webp-validation
   ```
3. Set up a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   # Windows: .\.venv\Scripts\Activate.ps1
   # Unix:    source .venv/bin/activate
   pip install -r requirements.txt
   cp .env.example .env
   ```
4. Make atomic, test-backed changes.
5. Verify quality gates locally:
   ```bash
   python -m unittest discover -s tests -v
   node .agents/skills/senior-repo-standards/scripts/audit-hygiene.js
   ```

---

## 4. Architectural Modifications & ADRs

If your change alters service boundaries, introduces external storage (e.g., S3/R2), adds authentication, or changes public API contracts:
1. Update the relevant blueprint in [`docs/architecture/`](./docs/architecture/).
2. Submit an **Architecture Decision Record (ADR)** in [`docs/adr/`](./docs/adr/) using [`ADR-000-template.md`](./docs/adr/ADR-000-template.md) and register it in [`docs/adr/README.md`](./docs/adr/README.md).

---

## 5. Submitting a Pull Request

1. Rebase onto the latest `main`:
   ```bash
   git checkout main
   git pull origin main
   git checkout your-branch
   git rebase main
   ```
2. Push your branch and open a PR using [`.github/PULL_REQUEST_TEMPLATE.md`](./.github/PULL_REQUEST_TEMPLATE.md).
3. Include test execution output as proof of verification.
4. Ensure all GitHub Actions CI checks pass before requesting review.
