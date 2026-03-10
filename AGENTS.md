# Repository Guidelines

## Project Structure & Module Organization
`src/` contains the backend: FastAPI routes in `src/api/`, capture and diff logic in `src/capture.py` and `src/diff.py`, orchestration in `src/pipeline.py`, and notifiers in `src/notify/`. The dashboard lives in `frontend/src/`, split into `pages/`, `components/`, and `api/client.ts`. Backend tests are in `tests/`. Database SQL lives in `migrations/`. Operational docs and design notes live in `docs/plans/`.

## Build, Test, and Development Commands
Use Docker for the main workflow:

- `make build` builds the multi-stage image.
- `make up` starts the app on `localhost:9900`.
- `make down` stops the stack.
- `make logs` tails container logs.
- `make check` triggers a manual check cycle in the container.

For local development:

- `uvicorn src.api.main:app --port 8000` runs the API.
- `python -m src.main --check-all` runs checks without the scheduler.
- `cd frontend && npm install && npm run dev` starts the Vite dashboard.
- `pytest tests/` runs the backend test suite.

## Coding Style & Naming Conventions
Use 4-space indentation in Python and keep existing type hints and async patterns intact. Follow snake_case for Python modules, functions, and test names such as `test_api_pages.py`. In the frontend, use PascalCase for React components and route files such as `PageDetail.tsx`, and lowercase names for support modules such as `client.ts`. No formatter or linter config is committed, so match the surrounding style and keep diffs small.

## Testing Guidelines
Tests are backend-only and use `pytest`. Add new tests under `tests/` with filenames matching `test_*.py`. Prefer focused unit tests for diffing, API behavior, and security-sensitive paths. Capture tests may require Playwright and Chromium; install them before running browser-dependent cases.

## Commit & Pull Request Guidelines
Recent history uses Conventional Commit-style subjects such as `feat(frontend): ...`, `fix(api): ...`, and `docs: ...`. Keep commit messages short, imperative, and scoped when useful. PRs should describe the behavior change, note any migration or env var impact, link the issue if one exists, and include screenshots for UI changes.

## Security & Configuration Tips
Do not commit real `.env` values, API keys, or Supabase credentials. When changing auth, snapshot file serving, or external notification logic, call out the operational impact in the PR.
