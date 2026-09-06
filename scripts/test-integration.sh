#!/usr/bin/env bash
# Запускает интеграционные тесты в изолированном Compose-проекте.

set -Eeuo pipefail

project_name="${PROJECT_NAME:-piecewise-linear-integration}"

compose() {
  # Выполняет команду изолированного Compose-проекта.
  docker compose --project-name "$project_name" -f compose.integration.yaml "$@"
}

cleanup() {
  # Удаляет контейнеры, сети и тома проверки.
  compose down --volumes --remove-orphans || true
}

trap cleanup EXIT

compose build
compose up --detach db
compose run --rm migrate
compose run --rm --no-deps tests
