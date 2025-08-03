"""
Модуль классификации ошибок с использованием LLM
"""

import json
import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import re

# Попытка импорта различных LLM провайдеров
try:
    from langchain.llms import Ollama
    from langchain.chat_models import ChatOllama
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False

try:
    import groq
    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class ErrorClassification:
    """Результат классификации ошибки"""
    application_type: str
    error_category: str
    severity: str
    keywords: List[str]
    confidence: float
    suggested_actions: List[str]

class ErrorClassifier:
    """Класс для классификации ошибок с помощью AI"""
    
    def __init__(self, llm_provider: str = "groq"):
        self.llm_provider = llm_provider
        self.llm = self._initialize_llm()
        
        # Паттерны для классификации ошибок
        self.error_patterns = {
            '1c': {
                'keywords': ['1с', '1c', 'конфигуратор', 'платформа', 'конфигурация'],
                'categories': {
                    'sql_errors': ['sql', 'запрос', 'база данных', 'суд', 'нарушение уникальности'],
                    'config_errors': ['конфигурация', 'не удалось найти процедуру', 'неопределенный тип'],
                    'rights_errors': ['недостаточно прав', 'доступ запрещен', 'нет права'],
                    'update_errors': ['обновление', 'версия', 'совместимость'],
                    'report_errors': ['отчет', 'печатная форма', 'шаблон']
                }
            },
            'windows': {
                'keywords': ['windows', 'система', 'bsod', 'синий экран', 'служба'],
                'categories': {
                    'system_errors': ['системная ошибка', 'критическая ошибка'],
                    'bsod_errors': ['синий экран', 'bsod', 'stop error'],
                    'service_errors': ['служба', 'service', 'не удалось запустить'],
                    'registry_errors': ['реестр', 'registry', 'ключ'],
                    'driver_errors': ['драйвер', 'driver', 'устройство']
                }
            },
            'office': {
                'keywords': ['excel', 'word', 'outlook', 'powerpoint', 'офис'],
                'categories': {
                    'excel_errors': ['excel', 'таблица', 'ячейка', 'формула'],
                    'word_errors': ['word', 'документ', 'шаблон'],
                    'outlook_errors': ['outlook', 'почта', 'email'],
                    'powerpoint_errors': ['powerpoint', 'презентация', 'слайд']
                }
            },
            'browser': {
                'keywords': ['chrome', 'firefox', 'edge', 'браузер', 'browser'],
                'categories': {
                    'connection_errors': ['соединение', 'connection', 'сеть'],
                    'javascript_errors': ['javascript', 'скрипт', 'script'],
                    'security_errors': ['безопасность', 'security', 'сертификат'],
                    'plugin_errors': ['плагин', 'plugin', 'расширение']
                }
            }
        }
    
    def _initialize_llm(self):
        """Инициализация LLM провайдера"""
        if self.llm_provider == "ollama" and OLLAMA_AVAILABLE:
            try:
                return ChatOllama(model="mistral:7b")
            except Exception as e:
                logger.warning(f"Не удалось инициализировать Ollama: {e}")
        
        elif self.llm_provider == "groq" and GROQ_AVAILABLE:
            try:
                import os
                api_key = os.getenv("GROQ_API_KEY")
                if not api_key:
                    logger.warning("GROQ_API_KEY не найден в переменных окружения")
                    return None
                return groq.Groq(api_key=api_key)
            except Exception as e:
                logger.warning(f"Не удалось инициализировать Groq: {e}")
        
        elif self.llm_provider == "openai" and OPENAI_AVAILABLE:
            try:
                import os
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    logger.warning("OPENAI_API_KEY не найден в переменных окружения")
                    return None
                return OpenAI(api_key=api_key)
            except Exception as e:
                logger.warning(f"Не удалось инициализировать OpenAI: {e}")
        
        logger.warning("LLM недоступен, будет использоваться правило-основанная классификация")
        return None
    
    def classify_error(self, error_text: str, error_info: Dict[str, str]) -> ErrorClassification:
        """
        Классификация ошибки
        
        Args:
            error_text: Текст ошибки
            error_info: Дополнительная информация об ошибке
            
        Returns:
            Результат классификации
        """
        try:
            # Сначала попробуем AI классификацию
            if self.llm:
                ai_result = self._classify_with_ai(error_text, error_info)
                if ai_result:
                    return ai_result
            
            # Fallback на правило-основанную классификацию
            return self._classify_with_rules(error_text, error_info)
            
        except Exception as e:
            logger.error(f"Ошибка при классификации: {e}")
            return self._get_default_classification()
    
    def _classify_with_ai(self, error_text: str, error_info: Dict[str, str]) -> Optional[ErrorClassification]:
        """Классификация с помощью AI"""
        try:
            prompt = self._create_classification_prompt(error_text, error_info)
            
            if isinstance(self.llm, groq.Groq):
                response = self.llm.chat.completions.create(
                    model="llama3.1-8b-8192",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1
                )
                result_text = response.choices[0].message.content
                
            elif isinstance(self.llm, OpenAI):
                response = self.llm.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1
                )
                result_text = response.choices[0].message.content
                
            else:  # Ollama
                result_text = self.llm.invoke(prompt)
            
            return self._parse_ai_response(result_text)
            
        except Exception as e:
            logger.error(f"Ошибка AI классификации: {e}")
            return None
    
    def _create_classification_prompt(self, error_text: str, error_info: Dict[str, str]) -> str:
        """Создание промпта для классификации"""
        return f"""
        Проанализируй ошибку и верни результат в JSON формате:
        
        Текст ошибки: {error_text}
        Дополнительная информация: {error_info}
        
        Определи:
        1. application_type: тип приложения (1c, windows, office, browser, other)
        2. error_category: категория ошибки (sql, config, rights, system, connection, etc.)
        3. severity: серьезность (low, medium, high, critical)
        4. keywords: ключевые слова для поиска решения (массив строк)
        5. confidence: уверенность в классификации (0-100)
        6. suggested_actions: предлагаемые действия (массив строк)
        
        Ответ должен быть в формате JSON:
        {{
            "application_type": "string",
            "error_category": "string", 
            "severity": "string",
            "keywords": ["string"],
            "confidence": number,
            "suggested_actions": ["string"]
        }}
        """
    
    def _parse_ai_response(self, response_text: str) -> Optional[ErrorClassification]:
        """Парсинг ответа AI"""
        try:
            # Извлечение JSON из ответа
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if not json_match:
                return None
            
            data = json.loads(json_match.group())
            
            return ErrorClassification(
                application_type=data.get('application_type', 'unknown'),
                error_category=data.get('error_category', 'unknown'),
                severity=data.get('severity', 'medium'),
                keywords=data.get('keywords', []),
                confidence=data.get('confidence', 50.0),
                suggested_actions=data.get('suggested_actions', [])
            )
            
        except Exception as e:
            logger.error(f"Ошибка парсинга AI ответа: {e}")
            return None
    
    def _classify_with_rules(self, error_text: str, error_info: Dict[str, str]) -> ErrorClassification:
        """Правило-основанная классификация"""
        text_lower = error_text.lower()
        
        # Определение типа приложения
        application_type = self._detect_application_type(text_lower, error_info)
        
        # Определение категории ошибки
        error_category = self._detect_error_category(text_lower, application_type)
        
        # Определение серьезности
        severity = self._detect_severity(text_lower)
        
        # Извлечение ключевых слов
        keywords = self._extract_keywords(text_lower, application_type)
        
        # Предлагаемые действия
        suggested_actions = self._get_suggested_actions(application_type, error_category)
        
        return ErrorClassification(
            application_type=application_type,
            error_category=error_category,
            severity=severity,
            keywords=keywords,
            confidence=70.0,  # Средняя уверенность для правила-основанной классификации
            suggested_actions=suggested_actions
        )
    
    def _detect_application_type(self, text: str, error_info: Dict[str, str]) -> str:
        """Определение типа приложения"""
        # Проверка информации из OCR
        if error_info.get('application'):
            return error_info['application']
        
        # Анализ текста
        for app_type, patterns in self.error_patterns.items():
            if any(keyword in text for keyword in patterns['keywords']):
                return app_type
        
        return 'unknown'
    
    def _detect_error_category(self, text: str, application_type: str) -> str:
        """Определение категории ошибки"""
        if application_type in self.error_patterns:
            categories = self.error_patterns[application_type]['categories']
            
            for category, keywords in categories.items():
                if any(keyword in text for keyword in keywords):
                    return category
        
        # Общие категории
        if any(word in text for word in ['sql', 'запрос', 'база данных']):
            return 'sql'
        elif any(word in text for word in ['права', 'доступ', 'permission']):
            return 'rights'
        elif any(word in text for word in ['соединение', 'connection', 'сеть']):
            return 'connection'
        elif any(word in text for word in ['файл', 'file', 'не найден']):
            return 'file'
        
        return 'unknown'
    
    def _detect_severity(self, text: str) -> str:
        """Определение серьезности ошибки"""
        critical_keywords = ['критическая', 'critical', 'fatal', 'синий экран', 'bsod']
        high_keywords = ['ошибка', 'error', 'failed', 'не удалось']
        medium_keywords = ['предупреждение', 'warning', 'внимание']
        
        if any(keyword in text for keyword in critical_keywords):
            return 'critical'
        elif any(keyword in text for keyword in high_keywords):
            return 'high'
        elif any(keyword in text for keyword in medium_keywords):
            return 'medium'
        
        return 'low'
    
    def _extract_keywords(self, text: str, application_type: str) -> List[str]:
        """Извлечение ключевых слов"""
        keywords = []
        
        # Добавление ключевых слов из паттернов
        if application_type in self.error_patterns:
            keywords.extend(self.error_patterns[application_type]['keywords'])
        
        # Извлечение кодов ошибок
        error_codes = re.findall(r'\b\d{3,5}\b|\b0x[0-9A-Fa-f]{8}\b', text)
        keywords.extend(error_codes)
        
        # Извлечение важных слов
        important_words = re.findall(r'\b\w{4,}\b', text)
        keywords.extend(important_words[:5])  # Первые 5 слов
        
        return list(set(keywords))  # Удаление дубликатов
    
    def _get_suggested_actions(self, application_type: str, error_category: str) -> List[str]:
        """Получение предлагаемых действий"""
        actions = {
            '1c': {
                'sql': ['Проверить SQL запрос', 'Проверить права доступа к базе данных'],
                'config': ['Проверить конфигурацию', 'Обновить конфигурацию'],
                'rights': ['Проверить права пользователя', 'Настроить роли доступа']
            },
            'windows': {
                'system': ['Перезагрузить систему', 'Проверить системные файлы'],
                'bsod': ['Проверить драйверы', 'Обновить систему'],
                'service': ['Перезапустить службу', 'Проверить зависимости службы']
            },
            'office': {
                'excel': ['Проверить формулы', 'Проверить ссылки на файлы'],
                'word': ['Проверить шаблон', 'Проверить макросы']
            }
        }
        
        if application_type in actions and error_category in actions[application_type]:
            return actions[application_type][error_category]
        
        return ['Проверить логи', 'Перезапустить приложение']
    
    def _get_default_classification(self) -> ErrorClassification:
        """Получение классификации по умолчанию"""
        return ErrorClassification(
            application_type='unknown',
            error_category='unknown',
            severity='medium',
            keywords=[],
            confidence=0.0,
            suggested_actions=['Проверить логи', 'Перезапустить приложение']
        ) 