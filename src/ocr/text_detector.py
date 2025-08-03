"""
Модуль детекции текстовых областей с помощью CRAFT
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional
import logging
from pathlib import Path

try:
    import torch
    import torch.nn.functional as F
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    logging.warning("PyTorch не установлен. CRAFT детекция недоступна.")

logger = logging.getLogger(__name__)

class TextDetector:
    """Класс для детекции текстовых областей с помощью CRAFT"""
    
    def __init__(self):
        self.craft_available = TORCH_AVAILABLE
        if self.craft_available:
            self._load_craft_model()
    
    def _load_craft_model(self):
        """Загрузка CRAFT модели"""
        try:
            # Здесь должна быть загрузка CRAFT модели
            # Для упрощения используем OpenCV детекцию
            logger.info("Используется OpenCV детекция текста")
        except Exception as e:
            logger.warning(f"Не удалось загрузить CRAFT модель: {e}")
            self.craft_available = False
    
    def detect_text_regions(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Детекция текстовых областей
        
        Args:
            image: Изображение для анализа
            
        Returns:
            Список координат текстовых областей (x, y, w, h)
        """
        if not self.craft_available:
            return self._detect_with_opencv(image)
        
        try:
            return self._detect_with_craft(image)
        except Exception as e:
            logger.error(f"Ошибка CRAFT детекции: {e}")
            return self._detect_with_opencv(image)
    
    def _detect_with_opencv(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Детекция текста с помощью OpenCV"""
        try:
            # Конвертация в оттенки серого
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Применение морфологических операций
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            morph = cv2.morphologyEx(gray, cv2.MORPH_CLOSE, kernel)
            
            # Поиск контуров
            contours, _ = cv2.findContours(morph, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            text_regions = []
            for contour in contours:
                # Фильтрация по размеру
                x, y, w, h = cv2.boundingRect(contour)
                if w > 20 and h > 10:  # Минимальный размер текстовой области
                    text_regions.append((x, y, w, h))
            
            return text_regions
            
        except Exception as e:
            logger.error(f"Ошибка OpenCV детекции: {e}")
            return []
    
    def _detect_with_craft(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """Детекция текста с помощью CRAFT (заглушка)"""
        # Здесь должна быть реализация CRAFT детекции
        # Пока используем OpenCV как fallback
        return self._detect_with_opencv(image)
    
    def crop_text_regions(self, image: np.ndarray, regions: List[Tuple[int, int, int, int]]) -> List[np.ndarray]:
        """
        Обрезка текстовых областей
        
        Args:
            image: Исходное изображение
            regions: Список координат областей
            
        Returns:
            Список обрезанных изображений
        """
        cropped_images = []
        
        for x, y, w, h in regions:
            # Добавление отступов
            padding = 5
            x1 = max(0, x - padding)
            y1 = max(0, y - padding)
            x2 = min(image.shape[1], x + w + padding)
            y2 = min(image.shape[0], y + h + padding)
            
            cropped = image[y1:y2, x1:x2]
            if cropped.size > 0:
                cropped_images.append(cropped)
        
        return cropped_images
    
    def merge_overlapping_regions(self, regions: List[Tuple[int, int, int, int]]) -> List[Tuple[int, int, int, int]]:
        """
        Объединение перекрывающихся областей
        
        Args:
            regions: Список координат областей
            
        Returns:
            Список объединенных областей
        """
        if not regions:
            return []
        
        # Сортировка по координате Y
        sorted_regions = sorted(regions, key=lambda r: r[1])
        
        merged = []
        current = sorted_regions[0]
        
        for region in sorted_regions[1:]:
            x1, y1, w1, h1 = current
            x2, y2, w2, h2 = region
            
            # Проверка перекрытия
            if (y1 <= y2 + h2 and y1 + h1 >= y2 and 
                x1 <= x2 + w2 and x1 + w1 >= x2):
                # Объединение областей
                x_min = min(x1, x2)
                y_min = min(y1, y2)
                x_max = max(x1 + w1, x2 + w2)
                y_max = max(y1 + h1, y2 + h2)
                current = (x_min, y_min, x_max - x_min, y_max - y_min)
            else:
                merged.append(current)
                current = region
        
        merged.append(current)
        return merged 