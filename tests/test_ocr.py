"""
Тесты для OCR модуля
"""

import pytest
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import sys
from pathlib import Path

# Добавление пути к модулям
sys.path.append(str(Path(__file__).parent.parent))

from src.ocr.image_preprocessor import ImagePreprocessor
from src.ocr.text_extractor import TextExtractor, OCRResult

class TestImagePreprocessor:
    """Тесты для предобработки изображений"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.preprocessor = ImagePreprocessor()
        self.test_image = self._create_test_image()
    
    def _create_test_image(self):
        """Создание тестового изображения"""
        # Создание изображения с текстом
        img = Image.new('RGB', (400, 200), color='white')
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("arial.ttf", 16)
        except:
            font = ImageFont.load_default()
        
        draw.text((50, 50), "Test Error Message", fill='black', font=font)
        return np.array(img)
    
    def test_preprocess_image(self):
        """Тест предобработки изображения"""
        processed = self.preprocessor.preprocess_image(self.test_image)
        
        assert processed is not None
        assert processed.shape == self.test_image.shape
        assert processed.dtype == np.uint8
    
    def test_detect_text_regions(self):
        """Тест обнаружения текстовых областей"""
        regions = self.preprocessor.detect_text_regions(self.test_image)
        
        assert isinstance(regions, list)
        # Должна быть хотя бы одна область с текстом
        assert len(regions) > 0
    
    def test_crop_error_region(self):
        """Тест обрезки области ошибки"""
        cropped = self.preprocessor.crop_error_region(self.test_image)
        
        assert cropped is not None
        assert cropped.shape[0] <= self.test_image.shape[0]
        assert cropped.shape[1] <= self.test_image.shape[1]

class TestTextExtractor:
    """Тесты для извлечения текста"""
    
    def setup_method(self):
        """Настройка перед каждым тестом"""
        self.extractor = TextExtractor()
        self.test_image = self._create_test_image()
    
    def _create_test_image(self):
        """Создание тестового изображения с ошибкой"""
        img = Image.new('RGB', (600, 300), color='white')
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("arial.ttf", 14)
        except:
            font = ImageFont.load_default()
        
        error_text = [
            "Error: Database connection failed",
            "Code: SQL-001",
            "Description: Unable to connect to database server"
        ]
        
        y = 50
        for line in error_text:
            draw.text((50, y), line, fill='black', font=font)
            y += 25
        
        return np.array(img)
    
    def test_extract_text(self):
        """Тест извлечения текста"""
        results = self.extractor.extract_text(self.test_image)
        
        assert isinstance(results, list)
        assert len(results) > 0
        
        for result in results:
            assert isinstance(result, OCRResult)
            assert result.text is not None
            assert result.confidence >= 0
            assert result.engine in ["tesseract", "easyocr"]
    
    def test_select_best_result(self):
        """Тест выбора лучшего результата OCR"""
        # Создание тестовых результатов
        results = [
            OCRResult(text="Error message", confidence=85.0, engine="tesseract", language="eng"),
            OCRResult(text="Error message", confidence=75.0, engine="easyocr", language="eng"),
            OCRResult(text="Some other text", confidence=90.0, engine="tesseract", language="eng")
        ]
        
        best = self.extractor.select_best_result(results)
        
        assert best is not None
        assert best.confidence >= 75.0  # Должен выбрать результат с ошибкой
    
    def test_extract_error_codes(self):
        """Тест извлечения кодов ошибок"""
        text = "Error SQL-001: Database connection failed. Error code: NET-002"
        codes = self.extractor.extract_error_codes(text)
        
        assert isinstance(codes, list)
        assert "SQL-001" in codes
        assert "NET-002" in codes
    
    def test_clean_text(self):
        """Тест очистки текста"""
        dirty_text = "  Error   message  \n  with  \t  spaces  "
        clean_text = self.extractor.clean_text(dirty_text)
        
        assert clean_text == "Error message with spaces"
    
    def test_extract_structured_error_info(self):
        """Тест извлечения структурированной информации об ошибке"""
        text = "Error SQL-001: Database connection failed in 1C application"
        info = self.extractor.extract_structured_error_info(text)
        
        assert isinstance(info, dict)
        assert "error_codes" in info
        assert "application" in info
        assert "message" in info

class TestOCRIntegration:
    """Интеграционные тесты OCR"""
    
    def test_full_ocr_pipeline(self):
        """Тест полного пайплайна OCR"""
        preprocessor = ImagePreprocessor()
        extractor = TextExtractor()
        
        # Создание тестового изображения
        img = Image.new('RGB', (500, 250), color='white')
        draw = ImageDraw.Draw(img)
        
        try:
            font = ImageFont.truetype("arial.ttf", 16)
        except:
            font = ImageFont.load_default()
        
        draw.text((50, 50), "Test Error: CONN-001", fill='black', font=font)
        draw.text((50, 80), "Connection timeout", fill='black', font=font)
        
        image_array = np.array(img)
        
        # Предобработка
        processed = preprocessor.preprocess_image(image_array)
        assert processed is not None
        
        # Извлечение текста
        results = extractor.extract_text(processed)
        assert len(results) > 0
        
        # Выбор лучшего результата
        best = extractor.select_best_result(results)
        assert best is not None
        assert "Error" in best.text or "CONN-001" in best.text
        
        # Извлечение структурированной информации
        info = extractor.extract_structured_error_info(best.text)
        assert "error_codes" in info 