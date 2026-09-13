.PHONY: install dev dev-all test test-unit test-integration lint format typecheck migrate migrate-create clean

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
	set -a && . ./.env.test && set +a && pytest

test-unit:
	pytest tests/unit

test-integration:
	pytest tests/integration

# NOTE: no tests/security/ directory exists yet in this repo.
# Add one and restore a `test-security: pytest tests/security` target
# once security-specific tests are written.

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

# NOTE: scripts/seed.py does not exist yet in this repo.
# Add it and restore a `seed: python scripts/seed.py` target once written.

clean:
	docker compose down -v
	find . -type d -name "__pycache__" -exec rm -r {} +
	find . -type d -name ".pytest_cache" -exec rm -r {} +
	find . -type d -name ".mypy_cache" -exec rm -r {} +
