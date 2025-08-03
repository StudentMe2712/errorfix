# 🚀 Быстрый старт

## Один скрипт для всего

```bash
# 1. Клонируйте репозиторий
git clone <repository-url>
cd error-screenshot-parser

# 2. Запустите установку
python setup.py

# 3. Запустите приложение
python run.py --mode streamlit
```

## Альтернативные способы запуска

### Docker (рекомендуется для продакшена)
```bash
# Сборка и запуск
docker-compose up

# Или только API
docker-compose --profile api up error-parser-api
```

### Ручная установка
```bash
# Установка зависимостей
pip install -r requirements.txt

# Создание .env
cp env.example .env

# Инициализация БД
python run.py --mode init-db

# Запуск
python run.py --mode streamlit
```

## Доступные команды

```bash
# Установка и настройка
python setup.py                    # Полная установка
make setup                        # То же самое через Makefile

# Запуск приложений
python run.py --mode streamlit    # Streamlit интерфейс
python run.py --mode fastapi      # API сервер
make run-streamlit                # Через Makefile
make run-api                      # Через Makefile

# Docker
make docker-build                 # Сборка образа
make docker-compose               # Запуск с Docker Compose
make docker-compose-api           # Только API

# Разработка
make format                       # Форматирование кода
make lint                         # Проверка линтером
make test                         # Запуск тестов
make clean                        # Очистка временных файлов
```

## Настройка API ключей

1. Откройте файл `.env`
2. Настройте один из провайдеров:

```bash
# Groq (рекомендуется)
GROQ_API_KEY=your_groq_api_key_here

# Или OpenAI
OPENAI_API_KEY=your_openai_api_key_here

# Или Ollama (локально)
OLLAMA_BASE_URL=http://localhost:11434
```

## Доступ к приложению

- **Streamlit**: http://localhost:8501
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## Поддерживаемые форматы

- PNG, JPG, JPEG, BMP, TIFF
- Максимальный размер: 10MB

## Поддерживаемые ошибки

- 1C (конфигуратор, платформа)
- Windows (системные ошибки, BSOD)
- Office (Excel, Word, Outlook)
- Браузеры (Chrome, Firefox, Edge)
- Антивирусы и утилиты

## Устранение проблем

### Tesseract не найден
```bash
# Windows
# Скачайте с https://github.com/UB-Mannheim/tesseract/wiki

# Linux
sudo apt-get install tesseract-ocr tesseract-ocr-rus

# macOS
brew install tesseract tesseract-lang
```

### Проблемы с зависимостями
```bash
# Обновите pip
python -m pip install --upgrade pip

# Переустановите зависимости
pip install -r requirements.txt --force-reinstall
```

### Проблемы с Docker
```bash
# Очистите кеш
docker system prune -a

# Пересоберите образ
docker-compose build --no-cache
```

## Полная документация

См. `README.md` для подробной документации. 