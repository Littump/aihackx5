BE := dev/backend
FE := dev/frontend
UV := uv run --project $(BE)
CONTRACT := dev/contracts/openapi.yaml
COMPOSE := $(shell docker compose version >/dev/null 2>&1 && echo docker compose || echo docker-compose)

.PHONY: setup up down test-db-reset migrate synth dev-be dev-fe test-be test-fe lint format check contract-types contract-check contract-lint demo langfuse-up langfuse-down langfuse-logs

setup:
	cd $(BE) && uv sync
	cd $(FE) && npm install
	uv tool install pre-commit >/dev/null 2>&1 || true
	pre-commit install
	test -f .env || cp .env.example .env

up:
	$(COMPOSE) up -d --wait

down:
	$(COMPOSE) down

test-db-reset:
	$(COMPOSE) exec -T postgres psql -U domovoy -d domovoy -c "DROP DATABASE IF EXISTS domovoy_test WITH (FORCE)" -c "CREATE DATABASE domovoy_test OWNER domovoy"

migrate:
	$(UV) python $(BE)/scripts/migrate.py

synth:
	$(UV) python -m app.synthetic --users 300 --weeks 10 --seed 42 --fraud-share 0.03

dev-be:
	cd $(BE) && uv run uvicorn app.main:app --reload --port 8000

dev-fe:
	cd $(FE) && npm run dev

test-be:
	cd $(BE) && uv run pytest -q

test-fe:
	cd $(FE) && npm run test -- --run

lint:
	cd $(BE) && uv run ruff check . && uv run ruff format --check . && uv run mypy app tests scripts
	cd $(FE) && npm run lint && npm run format:check && npm run typecheck
	python3 scripts/check_comments.py $(BE)/app $(BE)/tests $(BE)/scripts $(FE)/src scripts

format:
	cd $(BE) && uv run ruff check --fix . && uv run ruff format .
	cd $(FE) && npm run format && npm run lint:fix

check: lint

contract-lint:
	$(UV) python $(BE)/scripts/contract_lint.py $(CONTRACT)

contract-types:
	cd $(FE) && npm run contract-types

contract-check:
	$(UV) python $(BE)/scripts/contract_check.py $(CONTRACT)

LANGFUSE_COMPOSE := deploy/langfuse/docker-compose.yml

langfuse-up:
	$(COMPOSE) -f $(LANGFUSE_COMPOSE) up -d --wait
	@echo "Langfuse UI: http://localhost:3000  (admin@domovoy.local / domovoy-admin)"

langfuse-down:
	$(COMPOSE) -f $(LANGFUSE_COMPOSE) down

langfuse-logs:
	$(COMPOSE) -f $(LANGFUSE_COMPOSE) logs -f --tail=100 langfuse-web langfuse-worker

demo: up migrate synth
	@echo "TODO INF-005: eval + simulation + запуск"
