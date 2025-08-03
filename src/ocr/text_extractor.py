"""
Модуль извлечения текста с использованием нескольких OCR движков
"""

import pytesseract
import easyocr
import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
import logging
import re
from dataclasses import dataclass

try:
    from paddleocr import PaddleOCR
    PADDLEOCR_AVAILABLE = True
except ImportError:
    PADDLEOCR_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class OCRResult:
    """Результат OCR распознавания"""
    text: str
    confidence: float
    engine: str
    language: str
    bounding_boxes: Optional[List[Tuple[int, int, int, int]]] = None

class TextExtractor:
    """Класс для извлечения текста с изображений"""
    
    def __init__(self):
        # Настройка Tesseract
        self.tesseract_config = '--oem 3 --psm 6 -c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯабвгдеёжзийклмнопрстуфхцчшщъыьэюя.,!?;:()[]{}<>-_=+@#$%^&*|\\/"\'`~№'
        
        # Инициализация EasyOCR
        try:
            self.easyocr_reader = easyocr.Reader(['ru', 'en'], gpu=False)
        except Exception as e:
            logger.warning(f"Не удалось инициализировать EasyOCR: {e}")
            self.easyocr_reader = None
        
        # Инициализация PaddleOCR
        try:
            self.paddleocr_reader = PaddleOCR(use_angle_cls=True, lang='ch', use_gpu=False)
            logger.info("PaddleOCR инициализирован успешно")
        except Exception as e:
            logger.warning(f"Не удалось инициализировать PaddleOCR: {e}")
            self.paddleocr_reader = None
        
        # Поддерживаемые языки
        self.supported_languages = ['rus', 'eng']
        
        # Паттерны для обнаружения ошибок
        self.error_patterns = {
            'error_keywords': [
                r'ошибка', r'error', r'exception', r'исключение',
                r'failed', r'не удалось', r'не удалось выполнить',
                r'access denied', r'доступ запрещен',
                r'not found', r'не найдено', r'не существует',
                r'timeout', r'превышено время ожидания',
                r'connection', r'соединение', r'подключение'
            ],
            'error_codes': [
                r'\b\d{3,5}\b',  # Коды ошибок
                r'0x[0-9A-Fa-f]{8}',  # HEX коды
                r'[A-Z]{2,5}-\d{3,5}',  # Коды типа SQL-001
            ]
        }
    
    def extract_text(self, image: np.ndarray, use_multiple_engines: bool = True) -> List[OCRResult]:
        """
        Извлечение текста с изображения
        
        Args:
            image: Изображение для обработки
            use_multiple_engines: Использовать несколько OCR движков
            
        Returns:
            Список результатов OCR
        """
        results = []
        
        # Tesseract OCR
        try:
            tesseract_result = self._extract_with_tesseract(image)
            if tesseract_result:
                results.append(tesseract_result)
        except Exception as e:
            logger.error(f"Ошибка Tesseract OCR: {e}")
        
        # EasyOCR (если доступен)
        if use_multiple_engines and self.easyocr_reader:
            try:
                easyocr_result = self._extract_with_easyocr(image)
                if easyocr_result:
                    results.append(easyocr_result)
            except Exception as e:
                logger.error(f"Ошибка EasyOCR: {e}")
        
        # PaddleOCR (если доступен)
        if use_multiple_engines and PADDLEOCR_AVAILABLE and self.paddleocr_reader:
            try:
                paddleocr_result = self._extract_with_paddleocr(image)
                if paddleocr_result:
                    results.append(paddleocr_result)
            except Exception as e:
                logger.error(f"Ошибка PaddleOCR: {e}")
        
        return results
    
    def _extract_with_tesseract(self, image: np.ndarray) -> Optional[OCRResult]:
        """Извлечение текста с помощью Tesseract"""
        try:
            # Распознавание на русском и английском
            text_rus = pytesseract.image_to_string(
                image, lang='rus', config=self.tesseract_config
            )
            text_eng = pytesseract.image_to_string(
                image, lang='eng', config=self.tesseract_config
            )
            
            # Получение данных с уверенностью
            data_rus = pytesseract.image_to_data(
                image, lang='rus', config=self.tesseract_config, output_type=pytesseract.Output.DICT
            )
            data_eng = pytesseract.image_to_data(
                image, lang='eng', config=self.tesseract_config, output_type=pytesseract.Output.DICT
            )
            
            # Выбор лучшего результата
            if len(text_rus.strip()) > len(text_eng.strip()):
                text = text_rus
                data = data_rus
                language = 'rus'
            else:
                text = text_eng
                data = data_eng
                language = 'eng'
            
            # Расчет средней уверенности
            confidences = [int(conf) for conf in data['conf'] if int(conf) > 0]
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # Извлечение bounding boxes
            bounding_boxes = []
            for i in range(len(data['text'])):
                if int(data['conf'][i]) > 0:
                    x = data['left'][i]
                    y = data['top'][i]
                    w = data['width'][i]
                    h = data['height'][i]
                    bounding_boxes.append((x, y, w, h))
            
            return OCRResult(
                text=text.strip(),
                confidence=avg_confidence,
                engine='tesseract',
                language=language,
                bounding_boxes=bounding_boxes
            )
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении текста Tesseract: {e}")
            return None
    
    def _extract_with_easyocr(self, image: np.ndarray) -> Optional[OCRResult]:
        """Извлечение текста с помощью EasyOCR"""
        try:
            results = self.easyocr_reader.readtext(image)
            
            if not results:
                return None
            
            # Объединение всех найденных текстов
            texts = []
            bounding_boxes = []
            total_confidence = 0
            
            for (bbox, text, confidence) in results:
                if text.strip():
                    texts.append(text.strip())
                    bounding_boxes.append(bbox)
                    total_confidence += confidence
            
            combined_text = ' '.join(texts)
            avg_confidence = total_confidence / len(results) if results else 0
            
            # Определение языка (простая эвристика)
            russian_chars = len(re.findall(r'[а-яё]', combined_text.lower()))
            english_chars = len(re.findall(r'[a-z]', combined_text.lower()))
            
            language = 'rus' if russian_chars > english_chars else 'eng'
            
            return OCRResult(
                text=combined_text,
                confidence=avg_confidence * 100,  # Приведение к процентам
                engine='easyocr',
                language=language,
                bounding_boxes=bounding_boxes
            )
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении текста EasyOCR: {e}")
            return None
    
    def _extract_with_paddleocr(self, image: np.ndarray) -> Optional[OCRResult]:
        """Извлечение текста с помощью PaddleOCR"""
        try:
            # PaddleOCR автоматически определяет ориентацию
            results = self.paddleocr_reader.ocr(image, cls=True)
            
            if not results or not results[0]:
                return None
            
            texts = []
            bounding_boxes = []
            total_confidence = 0
            count = 0
            
            for line in results[0]:
                if len(line) >= 2:
                    bbox, (text, confidence) = line
                    if text.strip():
                        texts.append(text.strip())
                        bounding_boxes.append(bbox)
                        total_confidence += confidence
                        count += 1
            
            if not texts:
                return None
            
            combined_text = ' '.join(texts)
            avg_confidence = total_confidence / count if count > 0 else 0
            
            # Определение языка (простая эвристика)
            russian_chars = len(re.findall(r'[а-яё]', combined_text.lower()))
            english_chars = len(re.findall(r'[a-z]', combined_text.lower()))
            
            language = 'rus' if russian_chars > english_chars else 'eng'
            
            return OCRResult(
                text=combined_text,
                confidence=avg_confidence * 100,  # Приведение к процентам
                engine='paddleocr',
                language=language,
                bounding_boxes=bounding_boxes
            )
            
        except Exception as e:
            logger.error(f"Ошибка при извлечении текста PaddleOCR: {e}")
            return None
    
    def select_best_result(self, results: List[OCRResult]) -> Optional[OCRResult]:
        """
        Выбор лучшего результата из нескольких OCR движков
        
        Args:
            results: Список результатов OCR
            
        Returns:
            Лучший результат или None
        """
        if not results:
            return None
        
        # Сортировка по уверенности
        sorted_results = sorted(results, key=lambda x: x.confidence, reverse=True)
        
        # Дополнительная проверка на наличие ключевых слов ошибок
        for result in sorted_results:
            if self._contains_error_keywords(result.text):
                return result
        
        # Возврат результата с наивысшей уверенностью
        return sorted_results[0]
    
    def _contains_error_keywords(self, text: str) -> bool:
        """Проверка наличия ключевых слов ошибок в тексте"""
        text_lower = text.lower()
        
        for pattern in self.error_patterns['error_keywords']:
            if re.search(pattern, text_lower):
                return True
        
        return False
    
    def extract_error_codes(self, text: str) -> List[str]:
        """Извлечение кодов ошибок из текста"""
        error_codes = []
        
        for pattern in self.error_patterns['error_codes']:
            matches = re.findall(pattern, text, re.IGNORECASE)
            error_codes.extend(matches)
        
        return list(set(error_codes))  # Удаление дубликатов
    
    def clean_text(self, text: str) -> str:
        """Очистка и нормализация текста"""
        # Удаление лишних пробелов
        text = re.sub(r'\s+', ' ', text)
        
        # Удаление специальных символов (кроме важных для ошибок)
        text = re.sub(r'[^\w\s\-_.,!?;:()\[\]{}<>@#$%^&*|\\/"\'`~№]', '', text)
        
        # Нормализация переносов строк
        text = text.replace('\n', ' ').replace('\r', ' ')
        
        return text.strip()
    
    def extract_structured_error_info(self, text: str) -> Dict[str, str]:
        """
        Извлечение структурированной информации об ошибке
        
        Args:
            text: Распознанный текст
            
        Returns:
            Словарь с структурированной информацией
        """
        error_info = {
            'error_message': '',
            'error_code': '',
            'application': '',
            'timestamp': '',
            'stack_trace': ''
        }
        
        # Извлечение кода ошибки
        error_codes = self.extract_error_codes(text)
        if error_codes:
            error_info['error_code'] = error_codes[0]
        
        # Определение приложения по ключевым словам
        app_keywords = {
            '1c': ['1с', '1c', 'конфигуратор', 'платформа'],
            'windows': ['windows', 'система', 'bsod', 'синий экран'],
            'excel': ['excel', 'таблица', 'ячейка'],
            'word': ['word', 'документ'],
            'browser': ['chrome', 'firefox', 'edge', 'браузер'],
            'sql': ['sql', 'запрос', 'база данных', 'суд']
        }
        
        text_lower = text.lower()
        for app, keywords in app_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                error_info['application'] = app
                break
        
        # Извлечение основного сообщения об ошибке
        lines = text.split('\n')
        for line in lines:
            line = line.strip()
            if self._contains_error_keywords(line) and len(line) > 10:
                error_info['error_message'] = line
                break
        
        return error_info 