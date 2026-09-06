#!/usr/bin/env bash
# Единая точка входа для разработки, проверок и развёртывания проекта.

set -Eeuo pipefail

repository_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
command_name="${1:-help}"
revision="${2:-}"

show_help() {
  # Показывает доступные команды репозитория.
  cat <<'EOF'
Usage: bash ./project.sh <command> [revision]

  install           Установить зависимости и Chromium
  up                Запустить локальное Compose-окружение
  down              Остановить локальное Compose-окружение
  logs              Показать журналы Compose
  lint              Проверить стиль backend и frontend
  typecheck         Проверить типы backend и frontend
  check             Выполнить lint и typecheck
  test              Запустить unit- и frontend-тесты
  test-integration  Запустить integration-тесты в Compose
  e2e               Запустить E2E-тесты в Compose
  check-containers  Проверить production-образы и health endpoints
  verify            Выполнить все проверки
  migrate           Применить миграции
  migrate-down      Откатить миграции до указанной ревизии
  build             Собрать production-образы
  deploy            Запустить production-конфигурацию
EOF
}

run_lint() {
  # Запускает все проверки стиля.
  uv run --project backend ruff check backend
  uv run --project backend ruff format --check backend
  npm --prefix frontend run lint
}

run_typecheck() {
  # Запускает все проверки типов.
  uv run --project backend pyright --project backend
  npm --prefix frontend run typecheck
}

run_tests() {
  # Запускает быстрые тесты и проверку покрытия.
  uv run --project backend coverage run --rcfile=backend/pyproject.toml -m pytest backend/tests/unit
  uv run --project backend coverage report --rcfile=backend/pyproject.toml
  npm --prefix frontend run test
}

cd "$repository_root"

case "$command_name" in
  help) show_help ;;
  install)
    UV_LINK_MODE=copy uv sync --project backend --dev
    npm --prefix frontend ci
    npm --prefix frontend exec -- playwright install chromium
    ;;
  up) docker compose up --build ;;
  down) docker compose down ;;
  logs) docker compose logs --follow ;;
  lint) run_lint ;;
  typecheck) run_typecheck ;;
  check)
    run_lint
    run_typecheck
    ;;
  test) run_tests ;;
  test-integration) bash scripts/test-integration.sh ;;
  e2e) bash scripts/test-e2e.sh ;;
  check-containers) bash scripts/check-containers.sh ;;
  verify)
    run_lint
    run_typecheck
    run_tests
    bash scripts/test-integration.sh
    bash scripts/test-e2e.sh
    bash scripts/check-containers.sh
    ;;
  migrate) docker compose run --rm migrate ;;
  migrate-down)
    if [[ -z "$revision" ]]; then
      printf '%s\n' 'Для migrate-down нужна ревизия: make migrate-down REVISION=base' >&2
      exit 2
    fi
    docker compose run --rm migrate alembic downgrade "$revision"
    ;;
  build) docker compose -f compose.prod.yaml build ;;
  deploy) docker compose -f compose.prod.yaml up --build --detach ;;
  *)
    printf 'Неизвестная команда: %s\n' "$command_name" >&2
    show_help >&2
    exit 2
    ;;
esac
