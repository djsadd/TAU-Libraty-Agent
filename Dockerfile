# Базовый образ
FROM python:3.12.2-slim

# Переменные окружения
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Рабочая директория
WORKDIR /app

# Установим зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Скопируем код проекта
COPY . .

# Открываем порт для FastAPI
EXPOSE 8000

# По умолчанию запускаем uvicorn
# (в docker-compose для Dramatiq мы переопределим команду)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
