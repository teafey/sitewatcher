# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SiteWatcher is a visual web page change monitoring system. It captures screenshots and DOM text of websites on a schedule, detects pixel/text changes via diffing, and sends notifications (Telegram, Bitrix24). The UI is in Russian.

## Commands

### Docker (primary workflow)
```bash
make build          # docker compose build (multi-stage: Node frontend + Python backend)
make up             # docker compose up -d
make down           # docker compose down
make logs           # docker compose logs -f sitewatcher
make shell          # docker compose exec sitewatcher bash
make check          # trigger check-all cycle inside container
make restart        # docker compose restart sitewatcher
```

### Backend (Python)
```bash
pip install -r requirements.txt
playwright install chromium
python -m src.main --check-all          # check all active pages
python -m src.main --check-page <uuid>  # check single page
uvicorn src.api.main:app --port 8000    # run API server
pytest tests/                           # run all tests
pytest tests/test_diff.py               # run single test file
pytest tests/test_diff.py::test_identical_images_zero_diff  # single test
```

### Frontend (React)
```bash
cd frontend
npm install
npm run dev          # vite dev server (proxies /api and /static to localhost:9900)
npm run build        # tsc && vite build
```

## Architecture

### Deployment
Single Docker container serves both API and frontend. Docker maps port **9900 → 8000** internally. The frontend is built in a Node multi-stage step and served by FastAPI as static files with an SPA catch-all route. Container connects to external `supabase_default` network for DB access.

### Backend (`src/`)
- **`api/main.py`** — FastAPI app with APScheduler, API key auth middleware (`X-API-Key` header), CORS, lifespan management. Serves frontend from `frontend/dist/` with SPA catch-all
- **`api/routes/`** — REST endpoints for pages, snapshots, stats, and check triggers
- **`api/schemas.py`** — Pydantic v2 request/response models
- **`pipeline.py`** — Orchestrates the check cycle: capture → compare → notify (with retry/backoff). Bridges async FastAPI with sync Playwright via `ThreadPoolExecutor`
- **`capture.py`** — Playwright **sync** API: headless Chromium screenshots + DOM text extraction. Supports scroll-to-bottom, wait-for-selector, ignore-selectors, multi-viewport
- **`diff.py`** — Pixel diff (NumPy array comparison with tolerance) and text diff (unified_diff). Generates visual diff overlay images
- **`db.py`** — Async httpx client talking to Supabase REST API (`/rest/v1/`), no ORM
- **`notify/`** — Extensible notifiers via `BaseNotifier` abstract class (Telegram, Bitrix24)
- **`retention.py`** — Snapshot cleanup: keeps latest + up to 30 with changes
- **`config.py`** — pydantic-settings `Settings` from env vars
- **`main.py`** — CLI entry point with JSON logging setup

### Frontend (`frontend/src/`)
- React 18 + TypeScript + Vite + Tailwind CSS
- React Router v7 for client routing (`App.tsx`)
- `api/client.ts` — Axios client with API key from localStorage
- `pages/` — PagesList, PageDetail, PageForm, BulkImport
- `components/` — DiffViewer (3 modes: side-by-side, overlay slider, diff overlay), SnapshotTimeline, ImageSlider, TextDiff, StatusBar, PageCard, ViewportPresets

### Database (Supabase PostgreSQL)
- `pages` table — URL, name, viewports (JSONB array), check interval, diff threshold, ignore_selectors, scroll/wait options
- `snapshots` table — screenshot_path, dom_text/hash, diff_percent, diff_image_path, has_changes, viewport dimensions, error_message
- Migrations in `migrations/` (001–004: initial schema, seed, capture options, multi-viewport)

### Key data flow
`APScheduler` → `pipeline.run_check_cycle()` → for each active page: `capture.capture_page()` (Playwright in ThreadPoolExecutor) → `diff.compare()` (pixel + text) → `db.save_snapshot()` (Supabase REST) → `notify` if changes exceed threshold

## Configuration

Copy `.env.example` to `.env`. Key vars: `SUPABASE_URL`, `SUPABASE_KEY`, `API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `CHECK_INTERVAL_HOURS`, `DATA_DIR`, `DASHBOARD_URL`.

## Conventions

- Backend uses async/await throughout (httpx, FastAPI); Playwright is sync, wrapped in ThreadPoolExecutor
- Dataclasses for typed results (`CaptureResult`, `CompareResult`, `PixelDiffResult`, `TextDiffResult`)
- JSON logging with timestamps via custom `JsonFormatter`
- Snapshots stored as PNG files in `DATA_DIR` (mounted volume `/app/data`)
- No linting/formatting tools configured — no eslint, prettier, black, or flake8
- Tests are backend-only (pytest), located in `tests/`
