.DEFAULT_GOAL := help

.PHONY: help install up down logs lint typecheck check test test-integration e2e check-containers verify migrate migrate-down build deploy

help: ## Показать доступные команды
	bash ./project.sh help

install: ## Установить зависимости для локальной разработки
	bash ./project.sh install

up: ## Запустить локальное окружение с hot reload
	bash ./project.sh up

down: ## Остановить локальное окружение
	bash ./project.sh down

logs: ## Следить за журналами сервисов
	bash ./project.sh logs

lint: ## Проверить стиль backend и frontend
	bash ./project.sh lint

typecheck: ## Проверить типы backend и frontend
	bash ./project.sh typecheck

check: ## Выполнить все статические проверки
	bash ./project.sh check

test: ## Запустить тесты проекта
	bash ./project.sh test

test-integration: ## Запустить интеграционные тесты в изолированном Compose
	bash ./project.sh test-integration

e2e: ## Запустить Playwright в изолированном Compose
	bash ./project.sh e2e

check-containers: ## Проверить production-образы и health endpoints
	bash ./project.sh check-containers

verify: ## Выполнить полную проверку проекта
	bash ./project.sh verify

migrate: ## Применить миграции в локальном окружении
	bash ./project.sh migrate

migrate-down: ## Откатить миграции до REVISION (пример: REVISION=base)
	test -n "$(REVISION)"
	bash ./project.sh migrate-down $(REVISION)

build: ## Собрать production-образы
	bash ./project.sh build

deploy: ## Запустить production-конфигурацию
	bash ./project.sh deploy
