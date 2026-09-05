# Редактор ломаной линии

Одностраничное приложение для создания, редактирования и перестановки точек ломаной. Интерфейс на React сразу отражает изменения на графике, FastAPI сохраняет точки в PostgreSQL, а Alembic управляет схемой базы.

## Быстрый запуск

Для обычного локального запуска нужны только Docker Desktop (Windows/macOS) или Docker Engine с Compose plugin (Linux):

```bash
docker compose up --build
```

После запуска доступны:

- интерфейс — <http://localhost:5173>;
- API — <http://localhost:8000/api/v1>;
- Swagger UI — <http://localhost:8000/docs>;
- проверка процесса — <http://localhost:8000/api/v1/health/live>;
- проверка готовности базы — <http://localhost:8000/api/v1/health/ready>.

Compose сначала ждёт PostgreSQL, затем применяет миграции и только после этого запускает backend и Vite. Исходники подключены в контейнеры, поэтому изменения автоматически подхватываются. Остановка окружения:

```bash
docker compose down
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

## Локальные инструменты

Если Python 3.13, `uv`, Node.js 24 и GNU Make установлены на машине, доступны команды:

```bash
make help
make install
make check
make migrate
make build
```

Для отката миграции нужно явно указать ревизию, например `make migrate-down REVISION=base`. Команда `make test` предназначена для тестовых наборов после их добавления.

## Развёртывание на Linux

На сервере установите Docker Engine и Compose plugin, клонируйте репозиторий и подготовьте окружение:

```bash
cp .env.example .env
```

Обязательно замените `POSTGRES_PASSWORD` в `.env` на стойкий пароль. При необходимости задайте внешний `APP_PORT`. Затем запустите production-конфигурацию:

```bash
docker compose -f compose.prod.yaml up --build --detach
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
