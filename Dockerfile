# syntax=docker/dockerfile:1.7

# --- Stage: deps (кешируем установку зависимостей)
FROM python:3.12-slim AS deps
WORKDIR /app


# Ускоряем pip и ставим системные зависимости, если нужны (libpq-dev и т.п.)
ENV PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Если будете пользоваться psycopg2/brotli/etc — раскомментируйте нужные пакеты
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential gcc libpq-dev \
#  && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*


# --- Stage: runtime
FROM python:3.12-slim AS runtime
WORKDIR /app


ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UPLOAD_DIR=/data/uploads \
    DB_PATH=/app/data/app.db


# Создаём не-root пользователя
RUN useradd -m appuser
RUN mkdir -p "${UPLOAD_DIR}" && chown -R appuser:appuser "${UPLOAD_DIR}"

USER appuser

# Копируем зависимости из предыдущего слоя
COPY --from=deps /usr/local/lib/python3.12 /usr/local/lib/python3.12
COPY --from=deps /usr/local/bin /usr/local/bin

# Копируем код приложения
COPY --chown=appuser:appuser app ./app

# Открываем порт
EXPOSE 8000

# DEV-запуск: автосервер uvicorn
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# PROD-запуск: gunicorn + uvicorn worker (стабильнее под нагрузкой)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

