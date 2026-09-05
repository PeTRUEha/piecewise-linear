.DEFAULT_GOAL := help

.PHONY: help install up down logs lint typecheck check test migrate migrate-down build deploy

help: ## Показать доступные команды
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z_-]+:.*## / {printf "%-18s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Установить зависимости для локальной разработки
	uv sync --project backend --dev
	npm --prefix frontend ci

up: ## Запустить локальное окружение с hot reload
	docker compose up --build

down: ## Остановить локальное окружение
	docker compose down

logs: ## Следить за журналами сервисов
	docker compose logs --follow

lint: ## Проверить стиль backend и frontend
	uv run --project backend ruff check backend
	uv run --project backend ruff format --check backend
	npm --prefix frontend run lint

typecheck: ## Проверить типы backend и frontend
	uv run --project backend pyright --project backend
	npm --prefix frontend run typecheck

check: lint typecheck ## Выполнить все статические проверки

test: ## Запустить тесты проекта
	uv run --project backend pytest
	npm --prefix frontend run test

migrate: ## Применить миграции в локальном окружении
	docker compose run --rm migrate

migrate-down: ## Откатить миграции до REVISION (пример: REVISION=base)
	test -n "$(REVISION)"
	docker compose run --rm migrate alembic downgrade $(REVISION)

build: ## Собрать production-образы
	docker compose -f compose.prod.yaml build

deploy: ## Запустить production-конфигурацию
	docker compose -f compose.prod.yaml up --build --detach
