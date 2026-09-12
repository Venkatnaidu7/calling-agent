.PHONY: install dev dev-all test test-unit test-integration test-security lint format typecheck migrate migrate-create seed clean

install:
	pip install -e ".[dev]"
	cd apps/web && npm install

dev:
	docker compose up -d postgres redis
	uvicorn apps.api.main:app --reload

dev-all:
	docker compose up

test:
	docker compose -f docker-compose.yml -f docker-compose.test.yml up -d postgres redis
	pytest

test-unit:
	pytest tests/unit

test-integration:
	pytest tests/integration

test-security:
	pytest tests/security

lint:
	ruff check apps/ tests/

format:
	ruff format apps/ tests/

typecheck:
	mypy apps/api/

migrate:
	alembic upgrade head

migrate-create:
	alembic revision --autogenerate

seed:
	python scripts/seed.py

clean:
	docker compose down -v
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".mypy_cache" -exec rm -r {} +
