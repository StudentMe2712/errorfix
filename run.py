#!/usr/bin/env python3
"""
Основной скрипт для запуска умного парсера ошибок
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# Добавление пути к модулям
sys.path.append(str(Path(__file__).parent / "src"))

def setup_logging():
    """Настройка логирования"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('error_parser.log'),
            logging.StreamHandler()
        ]
    )

def check_dependencies():
    """Проверка зависимостей"""
    missing_deps = []
    
    try:
        import cv2
    except ImportError:
        missing_deps.append("opencv-python")
    
    try:
        import pytesseract
    except ImportError:
        missing_deps.append("pytesseract")
    
    try:
        import easyocr
    except ImportError:
        missing_deps.append("easyocr")
    
    try:
        import streamlit
    except ImportError:
        missing_deps.append("streamlit")
    
    if missing_deps:
        print("❌ Отсутствуют зависимости:")
        for dep in missing_deps:
            print(f"   - {dep}")
        print("\nУстановите их командой:")
        print("pip install -r requirements.txt")
        return False
    
    return True

def init_database():
    """Инициализация базы данных"""
    try:
        from database.init_db import init_sample_data
        print("🗄️ Инициализация базы данных...")
        init_sample_data()
        print("✅ База данных инициализирована")
        return True
    except Exception as e:
        print(f"❌ Ошибка инициализации базы данных: {e}")
        return False

def run_streamlit():
    """Запуск Streamlit приложения"""
    try:
        import subprocess
        import sys
        
        print("🚀 Запуск Streamlit приложения...")
        print("📱 Откройте браузер и перейдите по адресу: http://localhost:8501")
        print("⏹️ Для остановки нажмите Ctrl+C")
        
        # Запуск Streamlit
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "src/streamlit_app.py", "--server.port", "8501"
        ])
        
    except KeyboardInterrupt:
        print("\n👋 Приложение остановлено")
    except Exception as e:
        print(f"❌ Ошибка запуска Streamlit: {e}")

def run_fastapi():
    """Запуск FastAPI сервера"""
    try:
        import subprocess
        import sys
        
        print("🚀 Запуск FastAPI сервера...")
        print("📡 API доступен по адресу: http://localhost:8000")
        print("📚 Документация API: http://localhost:8000/docs")
        print("⏹️ Для остановки нажмите Ctrl+C")
        
        # Запуск FastAPI
        subprocess.run([
            sys.executable, "-m", "uvicorn", 
            "src.api.main:app", 
            "--host", "0.0.0.0", 
            "--port", "8000",
            "--reload"
        ])
        
    except KeyboardInterrupt:
        print("\n👋 API сервер остановлен")


def main():
    """Основная функция"""
    parser = argparse.ArgumentParser(description="Умный парсер скриншотов ошибок")
    parser.add_argument(
        "--mode", 
        choices=["streamlit", "fastapi", "init-db"], 
        default="streamlit",
        help="Режим запуска (по умолчанию: streamlit)"
    )
    parser.add_argument(
        "--check-deps", 
        action="store_true",
        help="Проверить зависимости"
    )
    
    args = parser.parse_args()
    
    # Настройка логирования
    setup_logging()
    
    print("🔍 Умный парсер скриншотов ошибок")
    print("=" * 50)
    
    # Проверка зависимостей
    if args.check_deps or not check_dependencies():
        if args.check_deps:
            return
        print("\n❌ Установите зависимости перед запуском")
        return
    
    # Инициализация базы данных
    if args.mode == "init-db":
        init_database()
        return
    
    # Проверка существования базы данных
    if not os.path.exists("solutions.db"):
        print("🗄️ База данных не найдена, инициализируем...")
        if not init_database():
            print("❌ Не удалось инициализировать базу данных")
            return
    
    # Запуск в выбранном режиме
    if args.mode == "streamlit":
        run_streamlit()
    elif args.mode == "fastapi":
        run_fastapi()

if __name__ == "__main__":
    main() 