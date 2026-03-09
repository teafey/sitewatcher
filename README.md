# SiteWatcher

Visual web page change monitoring system. SiteWatcher captures screenshots and DOM text of websites on a configurable schedule, detects pixel-level and text changes via diffing, and sends notifications through Telegram or Bitrix24.

> **Note:** The dashboard UI is in Russian.

## Features

- **Scheduled monitoring** -- configurable per-page check intervals (1--720 hours)
- **Pixel-level visual diff** -- NumPy-based image comparison with adjustable tolerance threshold
- **Text/DOM change detection** -- unified diff of extracted page text
- **Multi-viewport support** -- monitor pages at multiple resolutions (desktop, tablet, mobile)
- **Three diff viewing modes** -- side-by-side, overlay slider, diff overlay
- **Notifications** -- Telegram and Bitrix24 channels
- **Bulk import** -- add multiple pages at once
- **Snapshot timeline** -- browse historical snapshots with visual comparison
- **Self-monitoring** -- alerts when a scheduled check cycle is missed
- **Automatic retention** -- keeps latest snapshot + up to 30 with detected changes

## Tech Stack

| Layer | Technologies |
|---|---|
| **Backend** | Python 3.11, FastAPI, Playwright (Chromium), NumPy, Pillow, APScheduler, Pydantic v2, httpx |
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, React Router v7, Axios |
| **Database** | Supabase (PostgreSQL) via REST API |
| **Deployment** | Docker (multi-stage build), Docker Compose |

## Quick Start

### Prerequisites

- Docker and Docker Compose
- Supabase instance (local or cloud)

### 1. Clone and configure

```bash
git clone https://github.com/teafey/sitewatcher.git
cd sitewatcher
cp .env.example .env
```

Edit `.env` with your Supabase credentials and API key (see [Configuration](#configuration) below).

### 2. Set up the database

Run the migration files in your Supabase SQL Editor (Dashboard > SQL Editor > New Query), in order:

1. `migrations/001_initial.sql` -- creates tables
2. `migrations/002_seed.sql` -- optional test data
3. `migrations/003_capture_options.sql` -- scroll/wait fields
4. `migrations/004_multi_viewport.sql` -- multi-viewport support

Or via CLI:

```bash
psql "$DATABASE_URL" -f migrations/001_initial.sql
psql "$DATABASE_URL" -f migrations/002_seed.sql
psql "$DATABASE_URL" -f migrations/003_capture_options.sql
psql "$DATABASE_URL" -f migrations/004_multi_viewport.sql
```

### 3. Build and run

```bash
make build    # Build Docker image (~2-3 min, installs Playwright + Chromium)
make up       # Start container (port 9900)
```

### 4. Verify

```bash
curl http://localhost:9900/api/health
```

Expected response:

```json
{"status": "healthy", "last_run_at": null, "pages_checked": 0, "errors_count": 0, "uptime_seconds": 5.2}
```

Open the dashboard at `http://localhost:9900`.

## Configuration

Copy `.env.example` to `.env` and set the following variables:

| Variable | Required | Description | Default |
|---|---|---|---|
| `SUPABASE_URL` | Yes | Supabase API URL. For local Supabase: `http://kong:8000` | -- |
| `SUPABASE_KEY` | Yes | Supabase `service_role` key | -- |
| `API_KEY` | Yes | API key for authentication (sent as `X-API-Key` header) | -- |
| `TELEGRAM_BOT_TOKEN` | No | Telegram bot token for notifications | -- |
| `TELEGRAM_CHAT_ID` | No | Telegram chat/group ID for notifications | -- |
| `BITRIX_WEBHOOK_URL` | No | Bitrix24 webhook URL | -- |
| `DASHBOARD_URL` | No | Dashboard URL for links in notifications | `http://localhost:9900` |
| `CHECK_INTERVAL_HOURS` | No | Default check interval in hours | `24` |
| `DATA_DIR` | No | Path for storing screenshots | `./data` (`/app/data` in Docker) |

### Local vs Cloud Supabase

**Cloud Supabase**: Works out of the box — just set `SUPABASE_URL` and `SUPABASE_KEY` in `.env`.

**Local Supabase** (recommended for development): Start Supabase first with `npx supabase start`, then add the external network to `docker-compose.yml`:

```yaml
services:
  sitewatcher:
    networks:
      - supabase_default

networks:
  supabase_default:
    external: true
```

See [SETUP.md](SETUP.md) for detailed instructions.

## API Reference

All API endpoints (except `/api/health`) require the `X-API-Key` header matching the `API_KEY` environment variable.

### Health & Stats

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Health check (no auth required) |
| `GET` | `/api/stats` | Dashboard statistics |

### Pages

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/pages` | List all monitored pages |
| `POST` | `/api/pages` | Add a new page (triggers baseline capture) |
| `GET` | `/api/pages/:id` | Get page details |
| `PUT` | `/api/pages/:id` | Update page settings |
| `DELETE` | `/api/pages/:id` | Delete page and all its snapshots |

### Snapshots

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/snapshots/:page_id` | List snapshots (supports `limit`, `offset`, `changes_only`, `viewport_width`, `viewport_height` query params) |
| `GET` | `/api/snapshots/detail/:id` | Get snapshot metadata |
| `GET` | `/api/snapshots/detail/:id/screenshot` | Get screenshot image (PNG) |
| `GET` | `/api/snapshots/detail/:id/diff-image` | Get visual diff overlay image (PNG) |
| `GET` | `/api/snapshots/detail/:id/text-diff` | Get text diff (plain text) |
| `DELETE` | `/api/snapshots/detail/:id` | Delete a snapshot |

### Check Triggers

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/check` | Trigger check cycle for all active pages |
| `POST` | `/api/check/:page_id` | Trigger check for a single page |

### Example: Add a page

```bash
curl -X POST http://localhost:9900/api/pages \
  -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "name": "Example"}'
```

## Architecture

### Data Flow

```
APScheduler (interval)
  -> pipeline.run_check_cycle()
    -> for each active page:
      -> capture.capture_page()       # Playwright in ThreadPoolExecutor
      -> diff.compare()               # Pixel + text comparison
      -> db.save_snapshot()            # Supabase REST API
      -> notify (if changes > threshold)
```

### Backend (`src/`)

| Module | Purpose |
|---|---|
| `api/main.py` | FastAPI app, APScheduler, auth middleware, SPA serving |
| `api/routes/` | REST endpoints for pages, snapshots, stats, checks |
| `api/schemas.py` | Pydantic v2 request/response models |
| `pipeline.py` | Check cycle orchestration with retry/backoff |
| `capture.py` | Playwright sync API: screenshots + DOM text extraction |
| `diff.py` | Pixel diff (NumPy) and text diff (unified_diff) |
| `db.py` | Async httpx client for Supabase REST API |
| `notify/` | Notification channels (Telegram, Bitrix24) via `BaseNotifier` |
| `retention.py` | Snapshot cleanup policy |
| `config.py` | Settings from environment variables |
| `main.py` | CLI entry point |

### Frontend (`frontend/src/`)

| Module | Purpose |
|---|---|
| `App.tsx` | React Router configuration |
| `api/client.ts` | Axios client with API key from localStorage |
| `pages/` | PagesList, PageDetail, PageForm, BulkImport |
| `components/` | DiffViewer, SnapshotTimeline, ImageSlider, TextDiff, StatusBar, PageCard, ViewportPresets |

### Deployment

Single Docker container serves both the API and the frontend. The multi-stage Dockerfile builds the React frontend with Node, then bundles it into the Python image. FastAPI serves the built frontend as static files with an SPA catch-all route. Port mapping: **9900 (host) -> 8000 (container)**.

## Development

### Local backend

```bash
pip install -r requirements.txt
playwright install chromium
uvicorn src.api.main:app --port 8000    # API server
python -m src.main --check-all          # Manual check cycle
python -m src.main --check-page <uuid>  # Check single page
```

### Local frontend

```bash
cd frontend
npm install
npm run dev      # Vite dev server (proxies /api and /static to localhost:9900)
npm run build    # Production build
```

### Running tests

```bash
pytest tests/                           # All tests
pytest tests/test_diff.py               # Single file
pytest tests/test_diff.py::test_name    # Single test
```

### Make commands

| Command | Description |
|---|---|
| `make build` | Build Docker image |
| `make up` | Start container in background |
| `make down` | Stop container |
| `make logs` | Follow container logs |
| `make shell` | Open shell in container |
| `make check` | Trigger check-all cycle in container |
| `make restart` | Restart container |

## Project Structure

```
sitewatcher/
├── src/
│   ├── api/
│   │   ├── main.py              # FastAPI app, scheduler, middleware
│   │   ├── routes/
│   │   │   ├── pages.py         # Page CRUD endpoints
│   │   │   └── snapshots.py     # Snapshot & stats endpoints
│   │   └── schemas.py           # Pydantic models
│   ├── notify/
│   │   ├── base.py              # BaseNotifier abstract class
│   │   ├── telegram.py          # Telegram notifier
│   │   └── bitrix.py            # Bitrix24 notifier
│   ├── capture.py               # Playwright screenshot capture
│   ├── config.py                # Environment settings
│   ├── db.py                    # Supabase REST client
│   ├── diff.py                  # Image & text diffing
│   ├── main.py                  # CLI entry point
│   ├── pipeline.py              # Check cycle orchestration
│   └── retention.py             # Snapshot cleanup
├── frontend/
│   └── src/
│       ├── api/client.ts        # API client
│       ├── components/          # React components
│       └── pages/               # Route pages
├── migrations/
│   ├── 001_initial.sql          # Base schema
│   ├── 002_seed.sql             # Test data
│   ├── 003_capture_options.sql  # Scroll/wait options
│   └── 004_multi_viewport.sql   # Multi-viewport support
├── tests/                       # Backend tests (pytest)
├── Dockerfile                   # Multi-stage build
├── docker-compose.yml           # Container config
├── Makefile                     # Dev commands
├── requirements.txt             # Python dependencies
└── .env.example                 # Environment template
```

## Troubleshooting

| Problem | Solution |
|---|---|
| `network supabase_default not found` | Local Supabase is not running (`npx supabase start`), or you are using cloud Supabase -- remove the external network from `docker-compose.yml` |
| API returns `401 Unauthorized` | Missing `X-API-Key` header or value does not match `API_KEY` in `.env` |
| Screenshots not being created | Check logs (`make logs`) -- usually a URL access issue or Playwright/Chromium problem |
| Notifications not arriving | Telegram: verify `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`. The bot must be added to the chat |
| Port 9900 is busy | Change the port mapping in `docker-compose.yml`: `"8001:8000"` |

## License

[MIT](LICENSE)
