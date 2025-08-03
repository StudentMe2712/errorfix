"""
Модуль для парсинга текстовых файлов логов
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class LogParser:
    """Класс для парсинга логов из текстовых файлов"""
    
    def __init__(self):
        # Паттерны для различных типов логов
        self.log_patterns = {
            'error': [
                r'ERROR\s*\[.*?\]\s*(.*)',
                r'Exception:\s*(.*)',
                r'Error:\s*(.*)',
                r'FATAL\s*\[.*?\]\s*(.*)',
                r'CRITICAL\s*\[.*?\]\s*(.*)',
                r'ошибка.*?:\s*(.*)',
                r'исключение.*?:\s*(.*)',
            ],
            'warning': [
                r'WARN\s*\[.*?\]\s*(.*)',
                r'Warning:\s*(.*)',
                r'предупреждение.*?:\s*(.*)',
            ],
            'info': [
                r'INFO\s*\[.*?\]\s*(.*)',
                r'Information:\s*(.*)',
                r'информация.*?:\s*(.*)',
            ]
        }
        
        # Паттерны для извлечения контекста
        self.context_patterns = {
            'timestamp': r'(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2})',
            'process': r'\[PID:\s*(\d+)\]',
            'thread': r'\[Thread:\s*(\d+)\]',
            'user': r'\[User:\s*([^\]]+)\]',
            'module': r'\[Module:\s*([^\]]+)\]',
        }
    
    def parse_log_file(self, file_path: str) -> Dict[str, any]:
        """
        Парсинг лог файла
        
        Args:
            file_path: Путь к файлу логов
            
        Returns:
            Словарь с результатами парсинга
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return self.parse_log_content(content)
            
        except Exception as e:
            logger.error(f"Ошибка при парсинге лог файла {file_path}: {e}")
            return {'errors': [], 'warnings': [], 'info': [], 'context': {}}
    
    def parse_log_content(self, content: str) -> Dict[str, any]:
        """
        Парсинг содержимого логов
        
        Args:
            content: Содержимое лог файла
            
        Returns:
            Словарь с результатами парсинга
        """
        lines = content.split('\n')
        
        errors = []
        warnings = []
        info_messages = []
        context = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Поиск ошибок
            for pattern in self.log_patterns['error']:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    error_info = self._extract_error_info(line, match.group(1))
                    errors.append(error_info)
                    break
            
            # Поиск предупреждений
            for pattern in self.log_patterns['warning']:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    warning_info = self._extract_warning_info(line, match.group(1))
                    warnings.append(warning_info)
                    break
            
            # Поиск информационных сообщений
            for pattern in self.log_patterns['info']:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    info_info = self._extract_info_info(line, match.group(1))
                    info_messages.append(info_info)
                    break
        
        # Извлечение общего контекста
        context = self._extract_context(content)
        
        return {
            'errors': errors,
            'warnings': warnings,
            'info': info_messages,
            'context': context,
            'total_lines': len(lines),
            'error_count': len(errors),
            'warning_count': len(warnings),
            'info_count': len(info_messages)
        }
    
    def _extract_error_info(self, line: str, error_message: str) -> Dict[str, any]:
        """Извлечение информации об ошибке"""
        return {
            'message': error_message.strip(),
            'full_line': line,
            'timestamp': self._extract_timestamp(line),
            'severity': 'error',
            'error_codes': self._extract_error_codes(error_message),
            'context': self._extract_line_context(line)
        }
    
    def _extract_warning_info(self, line: str, warning_message: str) -> Dict[str, any]:
        """Извлечение информации о предупреждении"""
        return {
            'message': warning_message.strip(),
            'full_line': line,
            'timestamp': self._extract_timestamp(line),
            'severity': 'warning',
            'context': self._extract_line_context(line)
        }
    
    def _extract_info_info(self, line: str, info_message: str) -> Dict[str, any]:
        """Извлечение информации об информационном сообщении"""
        return {
            'message': info_message.strip(),
            'full_line': line,
            'timestamp': self._extract_timestamp(line),
            'severity': 'info',
            'context': self._extract_line_context(line)
        }
    
    def _extract_timestamp(self, line: str) -> Optional[str]:
        """Извлечение временной метки"""
        match = re.search(self.context_patterns['timestamp'], line)
        return match.group(1) if match else None
    
    def _extract_error_codes(self, text: str) -> List[str]:
        """Извлечение кодов ошибок"""
        error_codes = []
        
        # Паттерны для кодов ошибок
        patterns = [
            r'\b\d{3,5}\b',  # Числовые коды
            r'0x[0-9A-Fa-f]{8}',  # HEX коды
            r'[A-Z]{2,5}-\d{3,5}',  # Коды типа SQL-001
            r'Exception:\s*([A-Za-z]+Exception)',  # Типы исключений
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            error_codes.extend(matches)
        
        return list(set(error_codes))
    
    def _extract_line_context(self, line: str) -> Dict[str, any]:
        """Извлечение контекста из строки"""
        context = {}
        
        for key, pattern in self.context_patterns.items():
            match = re.search(pattern, line)
            if match:
                context[key] = match.group(1)
        
        return context
    
    def _extract_context(self, content: str) -> Dict[str, any]:
        """Извлечение общего контекста из всего файла"""
        context = {
            'file_size': len(content),
            'line_count': len(content.split('\n')),
            'first_timestamp': None,
            'last_timestamp': None,
            'processes': set(),
            'modules': set(),
            'users': set()
        }
        
        lines = content.split('\n')
        timestamps = []
        
        for line in lines:
            # Извлечение временных меток
            timestamp = self._extract_timestamp(line)
            if timestamp:
                timestamps.append(timestamp)
            
            # Извлечение процессов
            match = re.search(self.context_patterns['process'], line)
            if match:
                context['processes'].add(match.group(1))
            
            # Извлечение модулей
            match = re.search(self.context_patterns['module'], line)
            if match:
                context['modules'].add(match.group(1))
            
            # Извлечение пользователей
            match = re.search(self.context_patterns['user'], line)
            if match:
                context['users'].add(match.group(1))
        
        if timestamps:
            context['first_timestamp'] = min(timestamps)
            context['last_timestamp'] = max(timestamps)
        
        # Преобразование множеств в списки для JSON сериализации
        context['processes'] = list(context['processes'])
        context['modules'] = list(context['modules'])
        context['users'] = list(context['users'])
        
        return context
    
    def get_error_summary(self, parsed_logs: Dict[str, any]) -> Dict[str, any]:
        """
        Получение сводки по ошибкам
        
        Args:
            parsed_logs: Результат парсинга логов
            
        Returns:
            Сводка по ошибкам
        """
        errors = parsed_logs.get('errors', [])
        
        if not errors:
            return {'total_errors': 0, 'error_types': {}, 'most_common_errors': []}
        
        # Подсчет типов ошибок
        error_types = {}
        error_messages = []
        
        for error in errors:
            message = error['message']
            error_messages.append(message)
            
            # Определение типа ошибки
            error_type = self._classify_error_type(message)
            error_types[error_type] = error_types.get(error_type, 0) + 1
        
        # Наиболее частые ошибки
        from collections import Counter
        message_counter = Counter(error_messages)
        most_common = message_counter.most_common(5)
        
        return {
            'total_errors': len(errors),
            'error_types': error_types,
            'most_common_errors': [{'message': msg, 'count': count} for msg, count in most_common]
        }
    
    def _classify_error_type(self, error_message: str) -> str:
        """Классификация типа ошибки"""
        error_message_lower = error_message.lower()
        
        if any(word in error_message_lower for word in ['connection', 'network', 'timeout']):
            return 'network'
        elif any(word in error_message_lower for word in ['database', 'sql', 'query']):
            return 'database'
        elif any(word in error_message_lower for word in ['permission', 'access', 'denied']):
            return 'permission'
        elif any(word in error_message_lower for word in ['memory', 'out of memory']):
            return 'memory'
        elif any(word in error_message_lower for word in ['file', 'not found', 'path']):
            return 'file'
        else:
            return 'general' 