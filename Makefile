BE := dev/backend
FE := dev/frontend
UV := uv run --project $(BE)
CONTRACT := dev/contracts/openapi.yaml
COMPOSE := $(shell docker compose version >/dev/null 2>&1 && echo docker compose || echo docker-compose)

.PHONY: setup up down migrate synth dev-be dev-fe test-be test-fe lint format check contract-types contract-check contract-lint demo

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
	cd $(BE) && uv run ruff check . && uv run ruff format --check . && uv run mypy app
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

demo: up migrate synth
	@echo "TODO INF-005: eval + simulation + запуск"
