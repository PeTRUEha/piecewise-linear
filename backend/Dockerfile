# syntax=docker/dockerfile:1

FROM ghcr.io/astral-sh/uv:0.8.17 AS uv

FROM python:3.13-slim AS development
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app
ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy
COPY pyproject.toml uv.lock README.md ./
COPY src ./src
COPY alembic.ini ./
COPY migrations ./migrations
RUN uv sync --frozen --no-dev
EXPOSE 8000
CMD ["uvicorn", "piecewise_linear.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM development AS builder
RUN uv sync --frozen --no-dev --no-editable

FROM python:3.13-slim AS production
WORKDIR /app
ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/alembic.ini ./alembic.ini
COPY --from=builder /app/migrations ./migrations
EXPOSE 8000
CMD ["uvicorn", "piecewise_linear.main:app", "--host", "0.0.0.0", "--port", "8000"]
