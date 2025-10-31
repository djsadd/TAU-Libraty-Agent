# Базовый образ
FROM python:3.12.2-slim

RUN apt-get update && apt-get install -y libgl1 && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y poppler-utils

RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-rus \
    tesseract-ocr-kaz \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y ca-certificates && update-ca-certificates
# Переменные окружения
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN apt-get update && apt-get install -y openssh-client

# Установим системные зависимости
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    make \
    curl \
    git \
    libffi-dev \
    libssl-dev \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Установим Python-зависимости проекта
COPY new_requirements.txt .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r new_requirements.txt
    # && pip install torch --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt
    # && pip install torch --index-url https://download.pytorch.org/whl/cpu

#RUN pip install unstructured_inference
#RUN pip install pdf2image
# Скопируем код проекта
COPY . .


# Откроем порт
EXPOSE 8000
# Команда по умолчанию
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
