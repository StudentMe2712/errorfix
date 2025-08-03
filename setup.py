#!/usr/bin/env python3
"""
Скрипт для полной установки и настройки проекта
Запуск: python setup.py
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from typing import List, Tuple

def print_step(step: str):
    """Вывод шага установки"""
    print(f"\n🔧 {step}")
    print("=" * 50)

def check_python_version() -> bool:
    """Проверка версии Python"""
    print_step("Проверка версии Python")
    
    if sys.version_info < (3, 8):
        print("❌ Требуется Python 3.8 или выше")
        print(f"Текущая версия: {sys.version}")
        return False
    
    print(f"✅ Python {sys.version.split()[0]} - OK")
    return True

def install_dependencies() -> bool:
    """Установка зависимостей"""
    print_step("Установка зависимостей")
    
    try:
        # Установка основных зависимостей
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("✅ Основные зависимости установлены")
        
        # Установка в режиме разработки
        subprocess.run([sys.executable, "-m", "pip", "install", "-e", "."], 
                      check=True, capture_output=True)
        print("✅ Проект установлен в режиме разработки")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка установки зависимостей: {e}")
        return False

def create_env_file() -> bool:
    """Создание .env файла"""
    print_step("Настройка конфигурации")
    
    env_file = Path(".env")
    env_example = Path("env.example")
    
    if env_file.exists():
        print("✅ Файл .env уже существует")
        return True
    
    if not env_example.exists():
        print("❌ Файл env.example не найден")
        return False
    
    try:
        shutil.copy(env_example, env_file)
        print("✅ Файл .env создан из env.example")
        print("⚠️  Не забудьте настроить API ключи в .env файле")
        return True
    except Exception as e:
        print(f"❌ Ошибка создания .env: {e}")
        return False

def create_directories() -> bool:
    """Создание необходимых директорий"""
    print_step("Создание директорий")
    
    directories = [
        "data",
        "logs", 
        "uploads",
        "tests"
    ]
    
    try:
        for directory in directories:
            Path(directory).mkdir(exist_ok=True)
            print(f"✅ Создана директория: {directory}")
        return True
    except Exception as e:
        print(f"❌ Ошибка создания директорий: {e}")
        return False

def check_tesseract() -> bool:
    """Проверка Tesseract OCR"""
    print_step("Проверка Tesseract OCR")
    
    try:
        import pytesseract
        version = pytesseract.get_tesseract_version()
        print(f"✅ Tesseract {version} найден")
        return True
    except Exception as e:
        print("❌ Tesseract не найден")
        print("📥 Установите Tesseract:")
        print("   Windows: https://github.com/UB-Mannheim/tesseract/wiki")
        print("   Linux: sudo apt-get install tesseract-ocr")
        print("   macOS: brew install tesseract")
        return False

def init_database() -> bool:
    """Инициализация базы данных"""
    print_step("Инициализация базы данных")
    
    try:
        from src.database.init_db import init_sample_data
        init_sample_data()
        print("✅ База данных инициализирована")
        return True
    except Exception as e:
        print(f"❌ Ошибка инициализации БД: {e}")
        return False

def run_tests() -> bool:
    """Запуск тестов"""
    print_step("Запуск тестов")
    
    try:
        result = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-v"], 
                              capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Все тесты прошли успешно")
            return True
        else:
            print("⚠️  Некоторые тесты не прошли:")
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        print(f"❌ Ошибка запуска тестов: {e}")
        return False

def show_next_steps():
    """Показать следующие шаги"""
    print_step("Установка завершена!")
    print("\n🚀 Для запуска используйте:")
    print("   Streamlit: python run.py --mode streamlit")
    print("   API:       python run.py --mode fastapi")
    print("   Или:       make run-streamlit")
    print("   Или:       make run-api")
    print("\n📚 Документация:")
    print("   README.md - основная документация")
    print("   API docs:  http://localhost:8000/docs (после запуска API)")
    print("\n⚠️  Не забудьте:")
    print("   1. Настроить API ключи в .env файле")
    print("   2. Установить Tesseract OCR (если не установлен)")

def main():
    """Основная функция установки"""
    print("🔍 Умный парсер скриншотов ошибок")
    print("📦 Установка и настройка проекта")
    print("=" * 60)
    
    steps = [
        ("Проверка Python", check_python_version),
        ("Создание директорий", create_directories),
        ("Установка зависимостей", install_dependencies),
        ("Настройка .env", create_env_file),
        ("Проверка Tesseract", check_tesseract),
        ("Инициализация БД", init_database),
        ("Запуск тестов", run_tests),
    ]
    
    failed_steps = []
    
    for step_name, step_func in steps:
        if not step_func():
            failed_steps.append(step_name)
    
    if failed_steps:
        print(f"\n❌ Установка завершена с ошибками:")
        for step in failed_steps:
            print(f"   - {step}")
        print("\n🔧 Исправьте ошибки и запустите setup.py снова")
        return False
    else:
        show_next_steps()
        return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 