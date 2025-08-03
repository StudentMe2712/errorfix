"""
Конфигурация системы парсинга ошибок
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

class Config:
    """Центральная конфигурация приложения"""
    
    # Пути
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR / "data"
    LOGS_DIR = BASE_DIR / "logs"
    UPLOADS_DIR = BASE_DIR / "uploads"
    
    # База данных
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/error_parser.db")
    CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./data/chroma")
    
    # LLM настройки
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq")  # groq, ollama, openai
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
    
    # OCR настройки
    TESSERACT_CMD = os.getenv("TESSERACT_CMD", "tesseract")
    OCR_LANGUAGES = os.getenv("OCR_LANGUAGES", "rus+eng").split("+")
    OCR_CONFIDENCE_THRESHOLD = float(os.getenv("OCR_CONFIDENCE_THRESHOLD", "60.0"))
    
    # Веб-поиск
    SEARCH_TIMEOUT = int(os.getenv("SEARCH_TIMEOUT", "10"))
    MAX_SEARCH_RESULTS = int(os.getenv("MAX_SEARCH_RESULTS", "5"))
    SEARCH_SOURCES = [
        "stackoverflow.com",
        "docs.microsoft.com", 
        "support.microsoft.com",
        "1c.ru",
        "infostart.ru"
    ]
    
    # Логирование
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = os.getenv("LOG_FORMAT", "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}")
    LOG_FILE = LOGS_DIR / "error_parser.log"
    
    # API настройки
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    API_DEBUG = os.getenv("API_DEBUG", "false").lower() == "true"
    
    # Streamlit настройки
    STREAMLIT_PORT = int(os.getenv("STREAMLIT_PORT", "8501"))
    
    # Ограничения
    MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", "10")) * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".bmp", ".tiff"}
    
    # Redis настройки
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB = int(os.getenv("REDIS_DB", "0"))
    
    # Notion настройки
    NOTION_API_KEY = os.getenv("NOTION_API_KEY")
    NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
    
    # Obsidian настройки
    OBSIDIAN_VAULT_PATH = os.getenv("OBSIDIAN_VAULT_PATH", "./obsidian_vault")
    
    # Clipboard мониторинг
    ENABLE_CLIPBOARD_MONITORING = os.getenv("ENABLE_CLIPBOARD_MONITORING", "false").lower() == "true"
    
        @classmethod
    def create_directories(cls):
        """Создание необходимых директорий"""
        try:
            directories = [cls.DATA_DIR, cls.LOGS_DIR, cls.UPLOADS_DIR]
            for directory in directories:
                directory.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"⚠️  Предупреждение: не удалось создать директории: {e}")

    @classmethod
    def validate_config(cls) -> list[str]:
        """Валидация конфигурации"""
        errors = []
        
        # Проверка API ключей
        if cls.LLM_PROVIDER == "groq" and not cls.GROQ_API_KEY:
            errors.append("GROQ_API_KEY не установлен для провайдера groq")
        elif cls.LLM_PROVIDER == "openai" and not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY не установлен для провайдера openai")
        
        # Проверка Tesseract
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
        except Exception:
            errors.append("Tesseract OCR не установлен или не найден")
        
        return errors

# Создание директорий при импорте
Config.create_directories() 