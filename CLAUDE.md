# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SiteWatcher is a visual web page change monitoring system. It captures screenshots and DOM text of websites on a schedule, detects pixel/text changes via diffing, and sends notifications (Telegram, Bitrix24). The UI is in Russian.

## Commands

### Docker (primary workflow)
```bash
make build          # docker compose build
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
npm run dev          # vite dev server
npm run build        # tsc && vite build
```

## Architecture

### Backend (`src/`)
- **`api/main.py`** — FastAPI app with APScheduler, API key auth middleware, CORS, lifespan management
- **`api/routes/`** — REST endpoints for pages, snapshots, stats, and check triggers
- **`api/schemas.py`** — Pydantic request/response models
- **`pipeline.py`** — Orchestrates the check cycle: capture → compare → notify (with retry/backoff)
- **`capture.py`** — Playwright sync API: headless Chromium screenshots + DOM text extraction
- **`diff.py`** — Pixel diff (NumPy array comparison with tolerance) and text diff (unified_diff). Generates visual diff overlay images
- **`db.py`** — Async httpx client talking to Supabase REST API (`/rest/v1/`)
- **`notify/`** — Extensible notifiers via `BaseNotifier` abstract class (Telegram, Bitrix24)
- **`retention.py`** — Snapshot cleanup: keeps latest + up to 30 with changes
- **`config.py`** — pydantic-settings `Settings` from env vars
- **`main.py`** — CLI entry point

### Frontend (`frontend/src/`)
- React 18 + TypeScript + Vite + Tailwind CSS (dark theme)
- React Router for client routing (`App.tsx`)
- `api/client.ts` — Axios client with API key from localStorage
- `pages/` — PagesList, PageDetail, PageForm, BulkImport
- `components/` — DiffViewer (3 modes: side-by-side, overlay slider, diff overlay), SnapshotTimeline, ImageSlider, TextDiff, StatusBar

### Database (Supabase PostgreSQL)
- `pages` table — URL, viewport config, check interval, diff threshold, ignore_selectors
- `snapshots` table — screenshot_path, dom_text/hash, diff_percent, diff_image_path, text_diff, has_changes
- Migrations in `migrations/` (001_initial.sql, 002_seed.sql)

### Key data flow
`APScheduler` → `pipeline.run_check_cycle()` → for each active page: `capture.capture_page()` (Playwright) → `diff.compare()` (pixel + text) → save snapshot to DB → `notify` if changes exceed threshold

## Configuration

Copy `.env.example` to `.env`. Key vars: `SUPABASE_URL`, `SUPABASE_KEY`, `API_KEY`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `CHECK_INTERVAL_HOURS`, `DATA_DIR`.

## Conventions

- Backend uses async/await throughout (httpx, FastAPI)
- Dataclasses for typed results (`CaptureResult`, `CompareResult`, `PixelDiffResult`, `TextDiffResult`)
- JSON logging with timestamps
- Snapshots stored as files in `DATA_DIR` (mounted volume `/app/data`)
- App runs in a single Docker container connecting to an external Supabase network
