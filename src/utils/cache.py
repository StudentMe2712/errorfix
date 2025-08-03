"""
Модуль кэширования с использованием Redis
"""

import json
import hashlib
import logging
from typing import Any, Optional, Dict, List
from datetime import datetime, timedelta
import pickle

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("Redis не установлен. Кэширование недоступно.")

logger = logging.getLogger(__name__)

class CacheManager:
    """Менеджер кэширования с Redis"""
    
    def __init__(self, host: str = 'localhost', port: int = 6379, db: int = 0):
        self.redis_available = REDIS_AVAILABLE
        self.redis_client = None
        
        if self.redis_available:
            try:
                self.redis_client = redis.Redis(
                    host=host, 
                    port=port, 
                    db=db, 
                    decode_responses=False,
                    socket_connect_timeout=5,
                    socket_timeout=5
                )
                # Проверка подключения
                self.redis_client.ping()
                logger.info("Redis подключен успешно")
            except Exception as e:
                logger.warning(f"Не удалось подключиться к Redis: {e}")
                self.redis_available = False
    
    def _generate_key(self, prefix: str, data: Any) -> str:
        """Генерация ключа кэша"""
        if isinstance(data, str):
            content = data
        else:
            content = json.dumps(data, sort_keys=True)
        
        hash_value = hashlib.md5(content.encode()).hexdigest()
        return f"{prefix}:{hash_value}"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Получение значения из кэша
        
        Args:
            key: Ключ кэша
            
        Returns:
            Значение или None
        """
        if not self.redis_available or not self.redis_client:
            return None
        
        try:
            value = self.redis_client.get(key)
            if value:
                return pickle.loads(value)
            return None
        except Exception as e:
            logger.error(f"Ошибка получения из кэша: {e}")
            return None
    
    def set(self, key: str, value: Any, expire: int = 3600) -> bool:
        """
        Сохранение значения в кэш
        
        Args:
            key: Ключ кэша
            value: Значение для сохранения
            expire: Время жизни в секундах
            
        Returns:
            True если успешно
        """
        if not self.redis_available or not self.redis_client:
            return False
        
        try:
            serialized_value = pickle.dumps(value)
            return self.redis_client.setex(key, expire, serialized_value)
        except Exception as e:
            logger.error(f"Ошибка сохранения в кэш: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Удаление значения из кэша
        
        Args:
            key: Ключ кэша
            
        Returns:
            True если успешно
        """
        if not self.redis_available or not self.redis_client:
            return False
        
        try:
            return bool(self.redis_client.delete(key))
        except Exception as e:
            logger.error(f"Ошибка удаления из кэша: {e}")
            return False
    
    def clear_pattern(self, pattern: str) -> int:
        """
        Очистка кэша по паттерну
        
        Args:
            pattern: Паттерн ключей (например, "ocr:*")
            
        Returns:
            Количество удаленных ключей
        """
        if not self.redis_available or not self.redis_client:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Ошибка очистки кэша: {e}")
            return 0
    
    def cache_ocr_result(self, image_hash: str, ocr_results: List[Dict]) -> bool:
        """
        Кэширование результатов OCR
        
        Args:
            image_hash: Хеш изображения
            ocr_results: Результаты OCR
            
        Returns:
            True если успешно
        """
        key = self._generate_key("ocr", image_hash)
        return self.set(key, ocr_results, expire=86400)  # 24 часа
    
    def get_cached_ocr_result(self, image_hash: str) -> Optional[List[Dict]]:
        """
        Получение кэшированного результата OCR
        
        Args:
            image_hash: Хеш изображения
            
        Returns:
            Кэшированные результаты или None
        """
        key = self._generate_key("ocr", image_hash)
        return self.get(key)
    
    def cache_classification(self, text_hash: str, classification: Dict) -> bool:
        """
        Кэширование результатов классификации
        
        Args:
            text_hash: Хеш текста
            classification: Результат классификации
            
        Returns:
            True если успешно
        """
        key = self._generate_key("classification", text_hash)
        return self.set(key, classification, expire=3600)  # 1 час
    
    def get_cached_classification(self, text_hash: str) -> Optional[Dict]:
        """
        Получение кэшированной классификации
        
        Args:
            text_hash: Хеш текста
            
        Returns:
            Кэшированная классификация или None
        """
        key = self._generate_key("classification", text_hash)
        return self.get(key)
    
    def cache_search_results(self, query_hash: str, results: List[Dict]) -> bool:
        """
        Кэширование результатов поиска
        
        Args:
            query_hash: Хеш запроса
            results: Результаты поиска
            
        Returns:
            True если успешно
        """
        key = self._generate_key("search", query_hash)
        return self.set(key, results, expire=1800)  # 30 минут
    
    def get_cached_search_results(self, query_hash: str) -> Optional[List[Dict]]:
        """
        Получение кэшированных результатов поиска
        
        Args:
            query_hash: Хеш запроса
            
        Returns:
            Кэшированные результаты поиска или None
        """
        key = self._generate_key("search", query_hash)
        return self.get(key)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Получение статистики кэша
        
        Returns:
            Статистика кэша
        """
        if not self.redis_available or not self.redis_client:
            return {'available': False}
        
        try:
            info = self.redis_client.info()
            return {
                'available': True,
                'total_keys': info.get('db0', {}).get('keys', 0),
                'memory_usage': info.get('used_memory_human', 'N/A'),
                'uptime': info.get('uptime_in_seconds', 0)
            }
        except Exception as e:
            logger.error(f"Ошибка получения статистики кэша: {e}")
            return {'available': False, 'error': str(e)}
    
    def clear_all_cache(self) -> bool:
        """
        Очистка всего кэша
        
        Returns:
            True если успешно
        """
        if not self.redis_available or not self.redis_client:
            return False
        
        try:
            self.redis_client.flushdb()
            logger.info("Весь кэш очищен")
            return True
        except Exception as e:
            logger.error(f"Ошибка очистки кэша: {e}")
            return False 