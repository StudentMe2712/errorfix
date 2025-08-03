# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-rus \
    tesseract-ocr-eng \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Копируем файлы зависимостей
COPY requirements.txt .
COPY pyproject.toml .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir -e .

# Копируем исходный код
COPY . .

# Создаем необходимые директории
RUN mkdir -p data logs uploads

# Создаем пользователя для безопасности
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Открываем порты
EXPOSE 8000 8501

# Переменные окружения
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Команда по умолчанию
CMD ["python", "run.py", "--mode", "streamlit"] 