.PHONY: build up down logs shell check restart

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f sitewatcher

shell:
	docker compose exec sitewatcher bash

check:
	docker compose exec sitewatcher python -m src.main --check-all

restart:
	docker compose restart sitewatcher
