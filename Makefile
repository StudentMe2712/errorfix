.PHONY: help install test format lint clean run-streamlit run-api init-db

help: ## Показать справку
	@echo "Доступные команды:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Установить зависимости
	pip install -r requirements.txt
	pip install -e .[dev]

test: ## Запустить тесты
	pytest tests/ -v --cov=src --cov-report=html

test-fast: ## Запустить быстрые тесты
	pytest tests/ -v -m "not slow"

format: ## Форматировать код
	black src/ tests/
	isort src/ tests/

lint: ## Проверить код линтером
	flake8 src/ tests/
	black --check src/ tests/
	isort --check-only src/ tests/

clean: ## Очистить временные файлы
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -rf .coverage

run-streamlit: ## Запустить Streamlit приложение
	python run.py --mode streamlit

run-api: ## Запустить FastAPI сервер
	python run.py --mode fastapi

init-db: ## Инициализировать базу данных
	python run.py --mode init-db

check-deps: ## Проверить зависимости
	python run.py --check-deps

dev-setup: install init-db ## Полная настройка для разработки
	@echo "✅ Настройка завершена"
	@echo "🚀 Запустите: make run-streamlit или make run-api"

setup: ## Полная установка и настройка проекта
	python setup.py

docker-build: ## Собрать Docker образ
	docker build -t error-parser .

docker-run: ## Запустить в Docker
	docker run -p 8000:8000 -p 8501:8501 error-parser

docker-compose: ## Запустить с Docker Compose
	docker-compose up

docker-compose-api: ## Запустить только API с Docker Compose
	docker-compose --profile api up error-parser-api

all: format lint test ## Форматировать, проверить и протестировать 