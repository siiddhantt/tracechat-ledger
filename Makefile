.PHONY: dev up down lint-api test-api smoke-api lint-web typecheck-web

up:
	docker compose up --build

down:
	docker compose down

lint-api:
	cd apps/api && ruff check . && ruff format --check .

test-api:
	cd apps/api && pytest

smoke-api:
	cd apps/api && python scripts/smoke_api.py

smoke-api-asgi:
	cd apps/api && python scripts/smoke_asgi.py

lint-web:
	cd apps/web && npm run lint

typecheck-web:
	cd apps/web && npm run typecheck
