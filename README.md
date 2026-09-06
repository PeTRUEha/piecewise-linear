# Редактор ломаной линии

Одностраничное приложение для создания, редактирования и перестановки точек ломаной. Интерфейс на React сразу отражает изменения на графике, FastAPI сохраняет точки в PostgreSQL, а Alembic управляет схемой базы.

## Быстрый запуск

Поддерживаемая среда разработки — Ubuntu 24.04 WSL либо Linux с Docker Engine и Compose plugin. Docker Desktop не требуется.

На Windows сначала установите Ubuntu 24.04 WSL, затем откройте терминал Ubuntu. Рабочая копия хранится непосредственно в файловой системе WSL по пути:

```bash
/home/redmi/Python projects/piecewise-linear
```

Первичную установку системных инструментов выполняет сценарий от root; в Windows Terminal это можно сделать так:

```powershell
wsl -d Ubuntu-24.04 -u root -- bash -lc 'cd "/home/redmi/Python projects/piecewise-linear" && bash scripts/bootstrap-wsl.sh redmi'
```

После этого откройте Ubuntu заново, чтобы обновилось членство пользователя в группе `docker`. Все дальнейшие операции выполняйте внутри WSL из корня репозитория через `make`:

```bash
make install
make up
```

После запуска доступны:

- интерфейс — <http://localhost:5173>;
- API — <http://localhost:8000/api/v1>;
- Swagger UI — <http://localhost:8000/docs>;
- проверка процесса — <http://localhost:8000/api/v1/health/live>;
- проверка готовности базы — <http://localhost:8000/api/v1/health/ready>.

Compose сначала ждёт PostgreSQL, затем применяет миграции и только после этого запускает backend и Vite. Исходники подключены в контейнеры, поэтому изменения автоматически подхватываются. Остановка окружения:

```bash
make down
```

Порты и реквизиты локальной базы можно изменить через переменные из `.env.example`.

## API точек

Точка имеет только три поля: целочисленный `id` и конечные числовые координаты `x`, `y`. Порядок точек совпадает с возрастающим `id`.

| Метод | Путь | Назначение |
| --- | --- | --- |
| `GET` | `/api/v1/points` | Получить точки в текущем порядке |
| `POST` | `/api/v1/points` | Добавить точку; тело `{"x": 1, "y": 2}` |
| `PATCH` | `/api/v1/points/{id}` | Изменить координаты точки |
| `PUT` | `/api/v1/points/order` | Задать полный порядок; тело `{"ids": [3, 1, 2]}` |
| `DELETE` | `/api/v1/points/{id}` | Удалить точку и перенумеровать оставшиеся |

После любой операции, меняющей состав или порядок, сервер возвращает актуальное состояние. Если набор изменился до перестановки, API отвечает `409` и не сохраняет частичный результат.

## Команды разработки

Единый интерфейс проекта — Makefile. Каждая цель вызывает `project.sh` в Bash. Нативный запуск из Windows не поддерживается: используйте Ubuntu WSL или Linux.

```bash
make help
make install
make check
make test
make test-integration
make e2e
make check-containers
make verify
make migrate
make build
```

`make test` запускает модульные тесты backend с проверкой покрытия и компонентные тесты frontend. `make test-integration` сама создаёт изолированную PostgreSQL, применяет миграции, запускает тесты и удаляет окружение. `make e2e` аналогично поднимает полный Compose-сервис, ждёт frontend, запускает Playwright и очищает окружение. `make check-containers` проверяет production-образы и health endpoints. Для этих трёх команд также нужен Docker Compose.

`make verify` последовательно выполняет все статические, модульные, интеграционные, E2E- и контейнерные проверки. Процесс не зависит от Git-хостинга: любая внешняя система автоматизации может вызвать те же команды Make. Для отката миграции используйте `make migrate-down REVISION=base`.

## Развёртывание на Linux

На сервере установите Docker Engine и Compose plugin, клонируйте репозиторий и подготовьте окружение:

```bash
cp .env.example .env
```

Обязательно замените `POSTGRES_PASSWORD` в `.env` на стойкий пароль. При необходимости задайте внешний `APP_PORT`. Затем запустите production-конфигурацию:

```bash
make deploy
```

Nginx публикует интерфейс и проксирует API, Swagger и OpenAPI в backend. PostgreSQL и backend доступны только во внутренней сети Compose. Проверка состояния и просмотр журналов:

```bash
docker compose -f compose.prod.yaml ps
docker compose -f compose.prod.yaml logs --follow
```

Обновление выполняется повторным запуском команды `up --build --detach`: миграция должна успешно завершиться до перезапуска backend. Для остановки:

```bash
docker compose -f compose.prod.yaml down
```
