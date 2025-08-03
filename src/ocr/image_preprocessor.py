"""
Модуль предобработки изображений для улучшения качества OCR
"""

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter
import logging

logger = logging.getLogger(__name__)

class ImagePreprocessor:
    """Класс для предобработки изображений перед OCR"""
    
    def __init__(self):
        self.supported_formats = ['.png', '.jpg', '.jpeg', '.bmp', '.tiff']
    
    def preprocess_image(self, image_path: str) -> np.ndarray:
        """
        Основной метод предобработки изображения
        
        Args:
            image_path: Путь к изображению
            
        Returns:
            Обработанное изображение как numpy array
        """
        try:
            # Загрузка изображения
            if isinstance(image_path, str):
                image = cv2.imread(image_path)
            else:
                image = image_path
                
            if image is None:
                raise ValueError("Не удалось загрузить изображение")
            
            # Автоматическое определение и исправление ориентации
            image = self._fix_orientation(image)
            
            # Применение всех методов предобработки
            processed = self._apply_preprocessing_pipeline(image)
            
            return processed
            
        except Exception as e:
            logger.error(f"Ошибка при предобработке изображения: {e}")
            return image
    
    def _apply_preprocessing_pipeline(self, image: np.ndarray) -> np.ndarray:
        """Применение пайплайна предобработки"""
        
        # 1. Изменение размера (если слишком маленькое)
        image = self._resize_if_needed(image)
        
        # 2. Конвертация в оттенки серого
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # 3. Удаление шума
        denoised = self._denoise(gray)
        
        # 4. Улучшение контраста
        enhanced = self._enhance_contrast(denoised)
        
        # 5. Бинаризация
        binary = self._binarize(enhanced)
        
        # 6. Морфологические операции
        cleaned = self._morphological_operations(binary)
        
        return cleaned
    
    def _fix_orientation(self, image: np.ndarray) -> np.ndarray:
        """
        Автоматическое определение и исправление ориентации изображения
        
        Args:
            image: Исходное изображение
            
        Returns:
            Изображение с исправленной ориентацией
        """
        try:
            # Конвертация в оттенки серого для анализа
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            
            # Детекция линий для определения ориентации
            edges = cv2.Canny(gray, 50, 150, apertureSize=3)
            lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
            
            if lines is not None:
                # Анализ углов линий
                angles = []
                for rho, theta in lines[:10]:  # Берем первые 10 линий
                    angle = theta * 180 / np.pi
                    if angle < 45 or angle > 135:
                        angles.append(angle)
                
                if angles:
                    # Определение доминирующего угла
                    avg_angle = np.mean(angles)
                    
                    # Если угол значительно отличается от 0/90 градусов
                    if abs(avg_angle) > 5 and abs(avg_angle - 90) > 5:
                        # Поворот изображения
                        height, width = image.shape[:2]
                        center = (width // 2, height // 2)
                        
                        # Определение угла поворота
                        if avg_angle < 45:
                            rotation_angle = -avg_angle
                        else:
                            rotation_angle = 90 - avg_angle
                        
                        # Матрица поворота
                        rotation_matrix = cv2.getRotationMatrix2D(center, rotation_angle, 1.0)
                        rotated = cv2.warpAffine(image, rotation_matrix, (width, height))
                        
                        return rotated
            
            return image
            
        except Exception as e:
            logger.warning(f"Ошибка при определении ориентации: {e}")
            return image
    
    def _resize_if_needed(self, image: np.ndarray, min_width: int = 800) -> np.ndarray:
        """Изменение размера изображения если оно слишком маленькое"""
        height, width = image.shape[:2]
        
        if width < min_width:
            scale_factor = min_width / width
            new_width = int(width * scale_factor)
            new_height = int(height * scale_factor)
            image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_CUBIC)
            
        return image
    
    def _denoise(self, image: np.ndarray) -> np.ndarray:
        """Удаление шума с изображения"""
        # Нелокальное среднее для удаления шума
        denoised = cv2.fastNlMeansDenoising(image, None, 10, 7, 21)
        return denoised
    
    def _enhance_contrast(self, image: np.ndarray) -> np.ndarray:
        """Улучшение контраста изображения"""
        # CLAHE (Contrast Limited Adaptive Histogram Equalization)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(image)
        return enhanced
    
    def _binarize(self, image: np.ndarray) -> np.ndarray:
        """Бинаризация изображения"""
        # Адаптивная бинаризация
        binary = cv2.adaptiveThreshold(
            image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        return binary
    
    def _morphological_operations(self, image: np.ndarray) -> np.ndarray:
        """Морфологические операции для очистки"""
        # Создание ядра для морфологических операций
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        
        # Удаление мелких объектов
        cleaned = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
        cleaned = cv2.morphologyEx(cleaned, cv2.MORPH_OPEN, kernel)
        
        return cleaned
    
    def detect_text_regions(self, image: np.ndarray) -> list:
        """
        Обнаружение областей с текстом
        
        Args:
            image: Изображение для анализа
            
        Returns:
            Список координат областей с текстом
        """
        try:
            # Конвертация в оттенки серого
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if len(image.shape) == 3 else image
            
            # Применение фильтра Собеля для обнаружения краев
            sobel = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            sobel = np.uint8(np.absolute(sobel))
            
            # Бинаризация
            _, binary = cv2.threshold(sobel, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            # Поиск контуров
            contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            text_regions = []
            for contour in contours:
                # Фильтрация по размеру контура
                area = cv2.contourArea(contour)
                if area > 100:  # Минимальная площадь
                    x, y, w, h = cv2.boundingRect(contour)
                    # Фильтрация по соотношению сторон (текст обычно горизонтальный)
                    if w > h and w > 20 and h > 10:
                        text_regions.append((x, y, w, h))
            
            return text_regions
            
        except Exception as e:
            logger.error(f"Ошибка при обнаружении областей текста: {e}")
            return []
    
    def crop_error_region(self, image: np.ndarray, error_region: tuple) -> np.ndarray:
        """
        Обрезка области с ошибкой
        
        Args:
            image: Исходное изображение
            error_region: Координаты области (x, y, width, height)
            
        Returns:
            Обрезанное изображение
        """
        x, y, w, h = error_region
        return image[y:y+h, x:x+w]
    
    def save_processed_image(self, image: np.ndarray, output_path: str) -> bool:
        """
        Сохранение обработанного изображения
        
        Args:
            image: Обработанное изображение
            output_path: Путь для сохранения
            
        Returns:
            True если сохранение успешно
        """
        try:
            cv2.imwrite(output_path, image)
            return True
        except Exception as e:
            logger.error(f"Ошибка при сохранении изображения: {e}")
            return False 