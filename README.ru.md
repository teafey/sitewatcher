# SiteWatcher

Система визуального мониторинга изменений веб-страниц. Делает скриншоты сайтов по расписанию, определяет пиксельные и текстовые изменения и отправляет уведомления через Telegram и Bitrix24.

## Возможности

- **Скриншоты по расписанию** — автоматический захват страниц через Playwright (headless Chromium)
- **Пиксельный diff** — сравнение скриншотов с настраиваемым порогом чувствительности, генерация наложенного изображения различий
- **Текстовый diff** — сравнение DOM-текста в формате unified diff
- **Мульти-вьюпорт** — мониторинг страницы в нескольких разрешениях одновременно (desktop, tablet, mobile)
- **Уведомления** — Telegram и Bitrix24 при превышении порога изменений
- **React-дашборд** — список страниц, таймлайн снимков, три режима сравнения (бок о бок, слайдер, наложение diff)
- **Массовый импорт** — добавление нескольких URL одним запросом
- **Самомониторинг** — оповещение если цикл проверки был пропущен
- **Ретеншн** — автоматическая очистка старых снимков (хранит последний + до 30 с изменениями)

## Технологии

| Компонент | Стек |
|---|---|
| Бэкенд | Python 3.11, FastAPI, Playwright, NumPy, Pillow, httpx, APScheduler, Pydantic v2 |
| Фронтенд | React 18, TypeScript, Vite, Tailwind CSS, React Router v7, Axios |
| База данных | Supabase (PostgreSQL) |
| Инфраструктура | Docker (multi-stage build), Docker Compose |

## Быстрый старт

```bash
# 1. Клонировать репозиторий
git clone https://github.com/teafey/sitewatcher.git && cd sitewatcher

# 2. Запустить Supabase (если локальный)
npx supabase start

# 3. Применить миграции (в Supabase SQL Editor или через psql)
psql "$DATABASE_URL" -f migrations/001_initial.sql
psql "$DATABASE_URL" -f migrations/002_seed.sql
psql "$DATABASE_URL" -f migrations/003_capture_options.sql
psql "$DATABASE_URL" -f migrations/004_multi_viewport.sql

# 4. Настроить окружение
cp .env.example .env
# Заполнить SUPABASE_URL, SUPABASE_KEY, API_KEY

# 5. Собрать и запустить
make build
make up

# 6. Открыть дашборд
open http://localhost:9900
```

Подробная пошаговая инструкция — в [SETUP.md](SETUP.md).

## Установка и настройка

### Требования

- Docker и Docker Compose
- Supabase (локальный или облачный)

### Настройка Supabase

**Локальный Supabase** (рекомендуется для разработки):

```bash
npx supabase init
npx supabase start
```

После запуска в терминале появятся `API URL` и `service_role key` — они понадобятся для `.env`. Локальный Supabase создаёт Docker-сеть `supabase_default`, которую использует SiteWatcher.

**Облачный Supabase**: создать проект на [supabase.com](https://supabase.com), взять URL и service_role key из Settings → API. При облачном варианте необходимо убрать внешнюю сеть из `docker-compose.yml` (подробности в [SETUP.md](SETUP.md)).

### Миграции

Выполнить SQL-файлы в Supabase SQL Editor или через CLI:

```bash
psql "$DATABASE_URL" -f migrations/001_initial.sql
psql "$DATABASE_URL" -f migrations/002_seed.sql        # тестовые данные (опционально)
psql "$DATABASE_URL" -f migrations/003_capture_options.sql
psql "$DATABASE_URL" -f migrations/004_multi_viewport.sql
```

### Переменные окружения

```bash
cp .env.example .env
```

| Переменная | Обязательная | По умолчанию | Описание |
|---|---|---|---|
| `SUPABASE_URL` | да | — | URL Supabase API. Для локального: `http://kong:8000` |
| `SUPABASE_KEY` | да | — | Supabase `service_role` ключ |
| `API_KEY` | да | — | Ключ для защиты API (заголовок `X-API-Key`) |
| `TELEGRAM_BOT_TOKEN` | нет | — | Токен Telegram-бота |
| `TELEGRAM_CHAT_ID` | нет | — | ID чата/группы для уведомлений |
| `BITRIX_WEBHOOK_URL` | нет | — | URL вебхука Bitrix24 |
| `DASHBOARD_URL` | нет | `http://localhost:9900` | URL дашборда для ссылок в уведомлениях |
| `CHECK_INTERVAL_HOURS` | нет | `24` | Интервал проверок в часах |
| `DATA_DIR` | нет | `./data` (`/app/data` в Docker) | Путь для хранения скриншотов |

## Docker

Приложение упаковано в один Docker-контейнер (multi-stage build: Node для фронтенда + Python для бэкенда). Контейнер отдаёт и API, и собранный React-фронтенд.

### docker-compose.yml

```yaml
services:
  sitewatcher:
    build: .
    container_name: sitewatcher
    restart: unless-stopped
    ports:
      - "9900:8000"    # хост:контейнер
    volumes:
      - ./data:/app/data
    env_file:
      - .env
```

Порт **9900** на хосте маппится на **8000** внутри контейнера.

### Команды Makefile

| Команда | Описание |
|---|---|
| `make build` | Собрать Docker-образ |
| `make up` | Запустить контейнер в фоне |
| `make down` | Остановить контейнер |
| `make logs` | Показать логи в реальном времени |
| `make shell` | Открыть bash внутри контейнера |
| `make check` | Запустить проверку всех страниц |
| `make restart` | Перезапустить контейнер |

## Обзор API

Все API-эндпоинты (кроме `/api/health`) требуют заголовок `X-API-Key`.

### Страницы

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/api/pages` | Список всех страниц |
| `POST` | `/api/pages` | Создать страницу (автоматически делает базовый снимок) |
| `GET` | `/api/pages/:id` | Получить страницу по ID |
| `PUT` | `/api/pages/:id` | Обновить страницу |
| `DELETE` | `/api/pages/:id` | Удалить страницу и все снимки |

### Снимки

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/api/snapshots/:page_id` | Список снимков страницы (`limit`, `offset`, `changes_only`, `viewport_width`, `viewport_height`) |
| `GET` | `/api/snapshots/detail/:id` | Получить снимок по ID |
| `GET` | `/api/snapshots/detail/:id/screenshot` | Скачать скриншот (PNG) |
| `GET` | `/api/snapshots/detail/:id/diff-image` | Скачать изображение diff (PNG) |
| `GET` | `/api/snapshots/detail/:id/text-diff` | Получить текстовый diff |
| `DELETE` | `/api/snapshots/detail/:id` | Удалить снимок |

### Проверки

| Метод | Путь | Описание |
|---|---|---|
| `POST` | `/api/check` | Запустить проверку всех активных страниц |
| `POST` | `/api/check/:page_id` | Запустить проверку одной страницы |

### Система

| Метод | Путь | Описание |
|---|---|---|
| `GET` | `/api/health` | Статус здоровья (не требует API-ключа) |
| `GET` | `/api/stats` | Статистика: кол-во страниц, дата последнего снимка |

### Примеры

```bash
# Создать страницу для мониторинга
curl -X POST http://localhost:9900/api/pages \
  -H "X-API-Key: YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "url": "https://example.com",
    "name": "Пример",
    "diff_threshold": 0.5,
    "check_interval_hours": 12,
    "viewports": [
      {"width": 1920, "height": 1080},
      {"width": 375, "height": 812}
    ]
  }'

# Запустить проверку вручную
curl -X POST http://localhost:9900/api/check \
  -H "X-API-Key: YOUR_API_KEY"

# Проверить здоровье сервиса
curl http://localhost:9900/api/health
```

Ответ `/api/health`:

```json
{
  "status": "healthy",
  "last_run_at": "2026-03-09T12:00:00Z",
  "pages_checked": 5,
  "errors_count": 0,
  "uptime_seconds": 3600.0
}
```

## Архитектура

### Поток данных

```
APScheduler (по расписанию)
    |
    v
Pipeline.run_check_cycle()
    |
    |-- Capture (Playwright в ThreadPoolExecutor)
    |       скриншот + извлечение DOM-текста
    |
    |-- Diff (NumPy pixel diff + unified text diff)
    |       генерация изображения различий
    |
    |-- DB (Supabase REST API через httpx)
    |       сохранение снимка
    |
    +-- Notify (Telegram / Bitrix24)
            если diff_percent > threshold
```

### Бэкенд (`src/`)

| Модуль | Назначение |
|---|---|
| `api/main.py` | FastAPI-приложение, планировщик, middleware аутентификации, раздача фронтенда |
| `api/routes/pages.py` | CRUD-эндпоинты для страниц |
| `api/routes/snapshots.py` | Эндпоинты для снимков, скриншотов, diff-изображений, статистики |
| `api/schemas.py` | Pydantic v2 модели запросов/ответов |
| `pipeline.py` | Оркестрация цикла проверки: захват -> сравнение -> уведомление |
| `capture.py` | Playwright sync API: скриншоты + извлечение DOM (прокрутка, ожидание селекторов, игнорирование элементов) |
| `diff.py` | Пиксельный diff (NumPy) и текстовый diff (unified_diff), генерация overlay-изображения |
| `db.py` | Асинхронный httpx-клиент к Supabase REST API |
| `notify/` | Расширяемые нотификаторы: `BaseNotifier` -> `TelegramNotifier`, `BitrixNotifier` |
| `retention.py` | Очистка старых снимков (хранит последний + до 30 с изменениями) |
| `config.py` | Настройки из переменных окружения |
| `main.py` | CLI точка входа с JSON-логированием |

### Фронтенд (`frontend/src/`)

| Модуль | Назначение |
|---|---|
| `App.tsx` | Маршрутизация (React Router v7) |
| `api/client.ts` | Axios-клиент с API-ключом из localStorage |
| `pages/PagesList.tsx` | Список страниц с карточками |
| `pages/PageDetail.tsx` | Детальная страница: таймлайн снимков, сравнение |
| `pages/PageForm.tsx` | Форма создания/редактирования страницы |
| `pages/BulkImport.tsx` | Массовый импорт URL |
| `components/DiffViewer.tsx` | Три режима сравнения: бок о бок, слайдер наложения, diff overlay |
| `components/SnapshotTimeline.tsx` | Таймлайн снимков |
| `components/ImageSlider.tsx` | Слайдер для сравнения изображений |
| `components/TextDiff.tsx` | Визуализация текстовых различий |
| `components/PageCard.tsx` | Карточка страницы в списке |
| `components/ViewportPresets.tsx` | Пресеты разрешений экрана |
| `components/StatusBar.tsx` | Статусная строка |

### База данных

Две основные таблицы в Supabase PostgreSQL:

**pages** — отслеживаемые страницы:
- `id` (UUID), `url`, `name`, `viewport_width`, `viewport_height`, `viewports` (JSONB)
- `check_interval_hours`, `diff_threshold`, `ignore_selectors`, `wait_for_selector`
- `scroll_to_bottom`, `max_scrolls`, `wait_seconds`, `is_active`

**snapshots** — результаты проверок:
- `id` (UUID), `page_id` (FK -> pages), `screenshot_path`, `dom_text`, `dom_hash`
- `diff_percent`, `diff_image_path`, `text_diff`, `has_changes`, `error_message`
- `viewport_width`, `viewport_height`, `captured_at`

## Скриншоты

<!--
Добавьте скриншоты UI в папку docs/screenshots/ и раскомментируйте:

### Список страниц
![Список страниц](docs/screenshots/pages-list.png)

### Детальная страница с таймлайном
![Детальная страница](docs/screenshots/page-detail.png)

### Сравнение скриншотов (слайдер)
![Сравнение](docs/screenshots/diff-slider.png)

### Diff overlay
![Diff overlay](docs/screenshots/diff-overlay.png)
-->

*Скриншоты будут добавлены позже.*

## Разработка

### Структура проекта

```
sitewatcher/
├── src/                    # Бэкенд (Python)
│   ├── api/
│   │   ├── main.py         # FastAPI-приложение
│   │   ├── routes/         # REST-эндпоинты
│   │   └── schemas.py      # Pydantic-модели
│   ├── capture.py          # Playwright захват
│   ├── diff.py             # Пиксельный/текстовый diff
│   ├── pipeline.py         # Оркестрация проверок
│   ├── db.py               # Клиент Supabase
│   ├── notify/             # Уведомления
│   ├── retention.py        # Очистка снимков
│   ├── config.py           # Настройки
│   └── main.py             # CLI
├── frontend/               # Фронтенд (React)
│   ├── src/
│   │   ├── pages/          # Страницы приложения
│   │   ├── components/     # UI-компоненты
│   │   └── api/            # HTTP-клиент
│   └── package.json
├── migrations/             # SQL-миграции
├── tests/                  # Тесты (pytest)
├── docker-compose.yml
├── Dockerfile              # Multi-stage build
├── Makefile
├── requirements.txt
└── .env.example
```

### Локальная разработка фронтенда

```bash
cd frontend
npm install
npm run dev    # Vite dev-сервер с прокси на localhost:9900
```

### Тесты

```bash
# Внутри контейнера
make shell
pytest tests/

# На хосте
pip install -r requirements.txt
playwright install chromium
pytest tests/
```

## Диагностика проблем

| Проблема | Решение |
|---|---|
| `network supabase_default not found` | Локальный Supabase не запущен (`npx supabase start`), либо используется облачный — убрать внешнюю сеть из `docker-compose.yml` |
| API возвращает `401 Unauthorized` | Не передан заголовок `X-API-Key` или значение не совпадает с `API_KEY` в `.env` |
| Скриншоты не создаются | Проверить логи (`make logs`) — обычно проблема с доступом к URL или Playwright |
| Уведомления не приходят | Проверить `TELEGRAM_BOT_TOKEN` и `TELEGRAM_CHAT_ID`. Бот должен быть добавлен в чат |
| Порт 9900 занят | Изменить маппинг портов в `docker-compose.yml`: `"9901:8000"` |

## Лицензия

MIT
