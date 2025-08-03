"""
Централизованный логгер для системы
"""

import sys
from pathlib import Path
from loguru import logger

from config import Config

def setup_logger():
    """Настройка логгера"""
    
    # Удаление стандартного обработчика
    logger.remove()
    
    # Консольный вывод
    logger.add(
        sys.stdout,
        format=Config.LOG_FORMAT,
        level=Config.LOG_LEVEL,
        colorize=True
    )
    
    # Файловый вывод
    logger.add(
        Config.LOG_FILE,
        format=Config.LOG_FORMAT,
        level=Config.LOG_LEVEL,
        rotation="1 day",
        retention="7 days",
        compression="zip"
    )
    
    # Отладочный файл (только для DEBUG)
    if Config.LOG_LEVEL == "DEBUG":
        debug_file = Config.LOGS_DIR / "debug.log"
        logger.add(
            debug_file,
            format=Config.LOG_FORMAT,
            level="DEBUG",
            rotation="1 day",
            retention="3 days"
        )
    
    logger.info("Логгер настроен")

def get_logger(name: str = None):
    """Получение логгера для модуля"""
    if name:
        return logger.bind(module=name)
    return logger

# Автоматическая настройка при импорте
setup_logger() 