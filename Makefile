.DEFAULT_GOAL := help

SHELL := /bin/bash
.SHELLFLAGS := -Eeuo pipefail -c

.PHONY: help install up down logs lint typecheck check test test-integration e2e check-containers verify migrate migrate-down build deploy

help: ## Показать доступные команды
	@grep -E '^[a-z-]+:.*##' Makefile | sed -E 's/:.*##/  /'

install: ## Установить зависимости для локальной разработки
	UV_LINK_MODE=copy uv sync --project backend --dev
	npm --prefix frontend ci
	npm --prefix frontend exec -- playwright install chromium

up: ## Запустить локальное окружение с hot reload
	docker compose up --build

down: ## Остановить локальное окружение
	docker compose down

logs: ## Следить за журналами Compose
	docker compose logs --follow

lint: ## Проверить стиль backend и frontend
	uv run --project backend ruff check backend
	uv run --project backend ruff format --check backend
	npm --prefix frontend run lint

typecheck: ## Проверить типы backend и frontend
	uv run --project backend pyright --project backend
	npm --prefix frontend run typecheck

check: ## Выполнить все статические проверки
	$(MAKE) lint
	$(MAKE) typecheck

test: ## Запустить тесты проекта
	uv run --project backend coverage run --rcfile=backend/pyproject.toml -m pytest backend/tests/unit
	uv run --project backend coverage report --rcfile=backend/pyproject.toml
	npm --prefix frontend run test

test-integration: ## Запустить интеграционные тесты в изолированном Compose
	bash scripts/test-integration.sh

e2e: ## Запустить Playwright в изолированном Compose
	bash scripts/test-e2e.sh

check-containers: ## Проверить production-образы и health endpoints
	bash scripts/check-containers.sh

verify: ## Выполнить полную проверку проекта
	$(MAKE) check
	$(MAKE) test
	$(MAKE) test-integration
	$(MAKE) e2e
	$(MAKE) check-containers

migrate: ## Применить миграции в локальном окружении
	docker compose run --rm migrate

migrate-down: ## Откатить миграции до REVISION (пример: REVISION=base)
	test -n "$(REVISION)" || { printf '%s\n' 'Для migrate-down нужна ревизия: make migrate-down REVISION=base' >&2; exit 2; }
	docker compose run --rm migrate alembic downgrade $(REVISION)

build: ## Собрать production-образы
	docker compose -f compose.prod.yaml build

deploy: ## Запустить production-конфигурацию
	docker compose -f compose.prod.yaml up --build --detach