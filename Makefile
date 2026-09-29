.PHONY: up down logs test lint fmt migrate seed

up:
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f --tail=200

migrate:
	docker compose exec core python manage.py migrate

seed:
	docker compose exec core python manage.py shell < backend/core/scripts/seed_demo_tenant.py

test:
	docker compose exec core pytest
	docker compose exec api pytest

lint:
	ruff check backend
	mypy backend
	pnpm -r lint

fmt:
	ruff format backend
	pnpm -r format