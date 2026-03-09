# SETUP.md

Пошаговая инструкция по запуску SiteWatcher.

## Требования

- Docker и Docker Compose
- Supabase (локальный или облачный)

## 1. Настройка Supabase

### Вариант A: Облачный Supabase

1. Создать проект на [supabase.com](https://supabase.com)
2. Взять `URL` и `service_role key` из Settings → API

Работает с `docker-compose.yml` без изменений.

### Вариант B: Локальный Supabase (для разработки)

```bash
npx supabase init
npx supabase start
```

После запуска в терминале появятся `API URL` и `service_role key` — они понадобятся для `.env`.

Локальный Supabase создаёт Docker-сеть `supabase_default`. Чтобы SiteWatcher мог подключиться, добавьте в `docker-compose.yml`:

```yaml
services:
  sitewatcher:
    # ... существующие настройки ...
    networks:
      - supabase_default

networks:
  supabase_default:
    external: true
```

## 2. Применение миграций

Выполнить SQL-файлы **по порядку** в Supabase SQL Editor (Dashboard → SQL Editor → New Query):

1. **Создание таблиц** — `migrations/001_initial.sql`
2. **Тестовые данные** (опционально) — `migrations/002_seed.sql`
3. **Настройки захвата** — `migrations/003_capture_options.sql` (scroll, wait)
4. **Мульти-viewport** — `migrations/004_multi_viewport.sql` (несколько разрешений экрана)

Или через CLI:

```bash
psql "$DATABASE_URL" -f migrations/001_initial.sql
psql "$DATABASE_URL" -f migrations/002_seed.sql
psql "$DATABASE_URL" -f migrations/003_capture_options.sql
psql "$DATABASE_URL" -f migrations/004_multi_viewport.sql
```

## 3. Настройка окружения

```bash
cp .env.example .env
```

Заполнить `.env`:

| Переменная | Обязательная | Описание |
|---|---|---|
| `SUPABASE_URL` | да | URL Supabase API. Для локального: `http://kong:8000` |
| `SUPABASE_KEY` | да | Supabase `service_role` ключ |
| `API_KEY` | да | Произвольный ключ для защиты API (передаётся как `X-API-Key` header) |
| `TELEGRAM_BOT_TOKEN` | нет | Токен Telegram-бота для уведомлений |
| `TELEGRAM_CHAT_ID` | нет | ID чата/группы для уведомлений |
| `BITRIX_WEBHOOK_URL` | нет | URL вебхука Bitrix24 |
| `DASHBOARD_URL` | нет | URL дашборда для ссылок в уведомлениях (по умолчанию `http://localhost:9900`) |
| `CHECK_INTERVAL_HOURS` | нет | Интервал проверок в часах (по умолчанию `24`) |
| `DATA_DIR` | нет | Путь для хранения скриншотов (по умолчанию `./data`, в Docker = `/app/data`) |

## 4. Сборка и запуск

```bash
make build    # собрать Docker-образ (~2-3 мин, устанавливает Playwright + Chromium)
make up       # запустить контейнер (порт 9900 → 8000 внутри)
```

## 5. Проверка работоспособности

```bash
# Проверить что сервер запустился
curl http://localhost:9900/api/health

# Посмотреть логи
make logs
```

Ожидаемый ответ от `/api/health`:

```json
{"status": "healthy", "last_run_at": null, "pages_checked": 0, "errors_count": 0, "uptime_seconds": 5.2}
```

## 6. Первый запуск

### Добавить страницу для мониторинга

```bash
curl -X POST http://localhost:9900/api/pages \
  -H "X-API-Key: <ваш API_KEY из .env>" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "name": "Тестовая страница"}'
```

При создании страницы автоматически делается базовый снимок (скриншот + DOM).

### Запустить проверку вручную

```bash
# Проверить все активные страницы
make check

# Или проверить конкретную страницу через API
curl -X POST http://localhost:9900/api/check/<page_id> \
  -H "X-API-Key: <ваш API_KEY>"
```

### Открыть дашборд

Перейти в браузере на `http://localhost:9900` — откроется React-дашборд со списком страниц, таймлайном снимков и визуальным сравнением.

## 7. Запуск тестов

```bash
# Внутри контейнера
make shell
pytest tests/

# Один тест
pytest tests/test_diff.py::test_identical_images_zero_diff
```

Для запуска тестов на хосте (без Docker):

```bash
pip install -r requirements.txt
playwright install chromium
pytest tests/
```

## Диагностика проблем

| Проблема | Решение |
|---|---|
| `network supabase_default not found` | Используется локальный Supabase, но сеть не добавлена в `docker-compose.yml` (см. раздел 1, Вариант B), либо Supabase не запущен (`npx supabase start`) |
| API возвращает `401 Unauthorized` | Не передан заголовок `X-API-Key` или значение не совпадает с `API_KEY` в `.env` |
| Скриншоты не создаются | Проверить логи (`make logs`) — обычно проблема с доступом к URL или Playwright/Chromium |
| Уведомления не приходят | Telegram: проверить `TELEGRAM_BOT_TOKEN` и `TELEGRAM_CHAT_ID`. Бот должен быть добавлен в чат |
| Порт 9900 занят | Изменить маппинг портов в `docker-compose.yml`: `"9901:8000"` |
