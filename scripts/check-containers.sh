#!/usr/bin/env bash
# Проверяет production-образы и health endpoints в изолированном Compose-проекте.

set -Eeuo pipefail

port="${APP_PORT:-18080}"
project_name="${PROJECT_NAME:-piecewise-linear-check}"
export POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-container-check-only}"
export APP_PORT="$port"
base_url="http://127.0.0.1:${port}"

compose() {
  # Выполняет команду изолированного Compose-проекта.
  docker compose --project-name "$project_name" -f compose.prod.yaml "$@"
}

cleanup() {
  # Удаляет контейнеры, сети и тома проверки.
  compose down --volumes --remove-orphans || true
}

http_status() {
  # Возвращает HTTP-статус, включая ответы 4xx и 5xx.
  curl --silent --show-error --output /dev/null --write-out '%{http_code}' --max-time 15 "$1" || true
}

wait_for_status() {
  # Ожидает заданный HTTP-статус с ограниченным числом попыток.
  local url="$1"
  local expected_status="$2"
  local attempt
  for ((attempt = 1; attempt <= 30; attempt += 1)); do
    if [[ "$(http_status "$url")" == "$expected_status" ]]; then
      return
    fi
    sleep 1
  done
  printf '%s не вернул статус %s\n' "$url" "$expected_status" >&2
  return 1
}

trap cleanup EXIT

compose build
compose up --detach
wait_for_status "$base_url/api/v1/health/ready" 200
[[ "$(http_status "$base_url/api/v1/health/live")" == '200' ]]
compose exec -T backend python -c "import shutil, piecewise_linear; assert piecewise_linear.__file__; assert shutil.which('uv') is None"
compose exec -T frontend nginx -t
compose stop db
wait_for_status "$base_url/api/v1/health/ready" 503
[[ "$(http_status "$base_url/api/v1/health/live")" == '200' ]]
printf '%s\n' 'Проверка контейнеров и health endpoints пройдена'
