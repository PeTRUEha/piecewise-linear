#!/usr/bin/env bash
# Запускает Playwright против изолированного Compose-окружения.

set -Eeuo pipefail

frontend_port="${FRONTEND_PORT:-15173}"
backend_port="${BACKEND_PORT:-18000}"
postgres_port="${POSTGRES_PORT:-15432}"
project_name="${PROJECT_NAME:-piecewise-linear-e2e}"
export FRONTEND_PORT="$frontend_port"
export BACKEND_PORT="$backend_port"
export POSTGRES_PORT="$postgres_port"
export E2E_BASE_URL="http://127.0.0.1:${frontend_port}"

compose() {
  # Выполняет команду изолированного Compose-проекта.
  docker compose --project-name "$project_name" -f compose.yaml "$@"
}

cleanup() {
  # Удаляет контейнеры, сети и тома проверки.
  compose down --volumes --remove-orphans || true
}

wait_for_frontend() {
  # Ожидает готовности frontend перед запуском Playwright.
  local attempt
  for ((attempt = 1; attempt <= 60; attempt += 1)); do
    if curl --fail --silent --show-error --max-time 5 "$E2E_BASE_URL" > /dev/null; then
      return
    fi
    sleep 1
  done
  printf 'Frontend не стал доступен по адресу %s\n' "$E2E_BASE_URL" >&2
  return 1
}

trap cleanup EXIT

compose up --detach --build
wait_for_frontend
npm --prefix frontend run test:e2e
