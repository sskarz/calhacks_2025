# Repository Guidelines

## Project Structure & Module Organization
The FastAPI Etsy backend lives in `apis.py`, which wires in OAuth flows, websocket handlers, and file uploads. SQLite helpers sit in `db.py`; they create and mutate the `offersb.db` development database and should be reused instead of writing raw SQL in route handlers. The eBay sandbox harness is isolated in `ebay_api.py`, exposing another FastAPI app for inventory experiments. Static uploads and sample assets belong in `uploads/`, while Python dependencies are pinned in `requirements.txt`. Keep generated artifacts (tokens, cache files) out of version control—only check in source modules and supporting configs.

## Build, Test, and Development Commands
- `python -m venv .venv && source .venv/bin/activate` — create an isolated interpreter (required for consistent package versions).
- `pip install -r requirements.txt` — install FastAPI, Uvicorn, and supporting libraries.
- `uvicorn apis:app --reload --host 0.0.0.0 --port 8000` — run the Etsy backend with live reload.
- `uvicorn ebay_api:app --reload --port 8001` — expose the eBay sandbox utilities on a separate port.
- `python apis.py` — quick-start helper that boots the primary app with default settings.

## Coding Style & Naming Conventions
Follow standard PEP 8 conventions: 4-space indentation, snake_case for files, modules, functions, and descriptive CamelCase for Pydantic models. Keep FastAPI route declarations thin by moving reusable logic into helper functions or `db.py`. Annotate request/response models and function signatures with type hints to preserve FastAPI’s schema generation. Load secrets exclusively through `.env`; never commit credentials or long-lived tokens.

## Testing Guidelines
Automated tests are not yet committed; new work should introduce `pytest` suites under a `tests/` directory. Prefer high-level API tests that exercise FastAPI routes via `httpx.AsyncClient`, and unit tests for database helpers using temporary SQLite files. Ensure each test name describes the behavior under test (e.g., `test_authorize_returns_pkce_verifier`). Run `pytest -vv` locally before submitting changes, and document any manual smoke steps for OAuth flows.

## Commit & Pull Request Guidelines
Recent history favors short, present-tense summaries (e.g., `Update ebay_api OAuth callback`); continue that pattern and keep the subject under 72 characters. Group related edits into focused commits so reviewers can reason about each change set. Pull requests should include: a concise overview, linked issues or hackathon tasks, a checklist of verification steps (`uvicorn apis:app --reload`, `pytest -vv`), and screenshots or curl transcripts when endpoint behavior changes. Highlight any new environment variables or database migrations directly in the PR description.

## Security & Configuration Tips
Populate required Etsy and eBay credentials in `.env`; keep separate files per environment and never log client secrets. Rotate tokens frequently when pairing with third-party sandboxes, and clear `offersb.db` when sharing repositories to avoid leaking sample data. When adding new configuration toggles, document defaults in `README.md` and validate that missing variables fail fast with explicit exceptions.
