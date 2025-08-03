#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы системы
"""

import sys
import os
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import logging

# Добавление пути к модулям
sys.path.append(str(Path(__file__).parent / "src"))

def create_test_image():
    """Создание тестового изображения с ошибкой"""
    # Создание изображения
    width, height = 800, 600
    image = Image.new('RGB', (width, height), color='white')
    draw = ImageDraw.Draw(image)
    
    # Добавление текста ошибки
    try:
        # Попытка использовать системный шрифт
        font = ImageFont.truetype("arial.ttf", 16)
    except:
        # Fallback на стандартный шрифт
        font = ImageFont.load_default()
    
    error_text = [
        "Ошибка при выполнении запроса к базе данных",
        "",
        "Код ошибки: SQL-001",
        "Описание: Не удалось подключиться к серверу БД",
        "",
        "Возможные причины:",
        "- Неправильные настройки подключения",
        "- Сервер БД недоступен",
        "- Недостаточно прав доступа"
    ]
    
    y_position = 50
    for line in error_text:
        draw.text((50, y_position), line, fill='black', font=font)
        y_position += 30
    
    # Добавление рамки
    draw.rectangle([(30, 30), (width-30, height-30)], outline='red', width=2)
    
    return image

def test_ocr_module():
    """Тест OCR модуля"""
    print("🔍 Тестирование OCR модуля...")
    
    try:
        from ocr.image_preprocessor import ImagePreprocessor
        from ocr.text_extractor import TextExtractor
        
        # Создание тестового изображения
        test_image = create_test_image()
        test_image.save("test_error.png")
        print("✅ Тестовое изображение создано: test_error.png")
        
        # Предобработка
        preprocessor = ImagePreprocessor()
        processed_image = preprocessor.preprocess_image(np.array(test_image))
        print("✅ Предобработка изображения завершена")
        
        # Извлечение текста
        extractor = TextExtractor()
        ocr_results = extractor.extract_text(processed_image)
        
        if ocr_results:
            best_result = extractor.select_best_result(ocr_results)
            print(f"✅ OCR распознавание: {best_result.engine}")
            print(f"📝 Распознанный текст: {best_result.text[:100]}...")
            print(f"🎯 Уверенность: {best_result.confidence:.1f}%")
        else:
            print("❌ OCR не смог распознать текст")
            
    except Exception as e:
        print(f"❌ Ошибка тестирования OCR: {e}")

def test_ai_classifier():
    """Тест AI классификатора"""
    print("\n🤖 Тестирование AI классификатора...")
    
    try:
        from ai.error_classifier import ErrorClassifier
        
        classifier = ErrorClassifier(llm_provider="groq")
        
        # Тестовые данные
        test_error = "Ошибка при выполнении запроса к базе данных SQL-001"
        test_info = {"application": "1c", "error_code": "SQL-001"}
        
        classification = classifier.classify_error(test_error, test_info)
        
        print(f"✅ Классификация завершена:")
        print(f"   - Тип приложения: {classification.application_type}")
        print(f"   - Категория: {classification.error_category}")
        print(f"   - Серьезность: {classification.severity}")
        print(f"   - Уверенность: {classification.confidence:.1f}%")
        print(f"   - Ключевые слова: {classification.keywords}")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования AI: {e}")

def test_database():
    """Тест базы данных"""
    print("\n🗄️ Тестирование базы данных...")
    
    try:
        from database.knowledge_base import KnowledgeBase, Solution
        from datetime import datetime
        
        kb = KnowledgeBase()
        
        # Тестовое решение
        test_solution = Solution(
            id=None,
            error_text="Тестовая ошибка SQL-001",
            solution_text="Тестовое решение для проверки работы системы",
            application_type="1c",
            error_category="sql",
            source="Test",
            success_rate=90.0,
            created_at=datetime.now().isoformat(),
            tags=["тест", "sql", "1с"],
            steps=["Шаг 1", "Шаг 2", "Шаг 3"]
        )
        
        # Добавление решения
        if kb.add_solution(test_solution):
            print("✅ Тестовое решение добавлено в базу")
        else:
            print("❌ Ошибка добавления решения")
        
        # Поиск решений
        solutions = kb.search_solutions("SQL-001", "1c", limit=3)
        print(f"✅ Найдено решений: {len(solutions)}")
        
        # Статистика
        stats = kb.get_statistics()
        print(f"📊 Статистика: {stats.get('total_solutions', 0)} решений в базе")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования БД: {e}")

def test_web_search():
    """Тест веб-поиска"""
    print("\n🌐 Тестирование веб-поиска...")
    
    try:
        from search.web_search import WebSearch
        
        web_search = WebSearch()
        
        # Тестовый поиск
        results = web_search.search_solutions("SQL ошибка 1С", "1c", max_results=3)
        
        print(f"✅ Найдено результатов: {len(results)}")
        for i, result in enumerate(results, 1):
            print(f"   {i}. {result['title']}")
            print(f"      URL: {result['url']}")
            print(f"      Релевантность: {result['relevance']:.2f}")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования веб-поиска: {e}")

def test_full_pipeline():
    """Тест полного пайплайна"""
    print("\n🔄 Тестирование полного пайплайна...")
    
    try:
        from ocr.image_preprocessor import ImagePreprocessor
        from ocr.text_extractor import TextExtractor
        from ai.error_classifier import ErrorClassifier
        from database.knowledge_base import KnowledgeBase
        
        # Создание компонентов
        preprocessor = ImagePreprocessor()
        extractor = TextExtractor()
        classifier = ErrorClassifier(llm_provider="groq")
        kb = KnowledgeBase()
        
        # Создание тестового изображения
        test_image = create_test_image()
        image_array = np.array(test_image)
        
        # 1. Предобработка
        processed_image = preprocessor.preprocess_image(image_array)
        print("✅ Шаг 1: Предобработка завершена")
        
        # 2. OCR
        ocr_results = extractor.extract_text(processed_image)
        if not ocr_results:
            print("❌ OCR не смог распознать текст")
            return
            
        best_result = extractor.select_best_result(ocr_results)
        cleaned_text = extractor.clean_text(best_result.text)
        print(f"✅ Шаг 2: OCR завершен, распознано {len(cleaned_text)} символов")
        
        # 3. Извлечение структурированной информации
        error_info = extractor.extract_structured_error_info(cleaned_text)
        print(f"✅ Шаг 3: Извлечена информация: {error_info}")
        
        # 4. Классификация
        classification = classifier.classify_error(cleaned_text, error_info)
        print(f"✅ Шаг 4: Классификация: {classification.application_type} - {classification.error_category}")
        
        # 5. Поиск решений
        solutions = kb.search_solutions(cleaned_text, classification.application_type, limit=3)
        print(f"✅ Шаг 5: Найдено {len(solutions)} решений")
        
        print("\n🎉 Полный пайплайн работает корректно!")
        
    except Exception as e:
        print(f"❌ Ошибка тестирования пайплайна: {e}")

def main():
    """Основная функция тестирования"""
    print("🧪 Тестирование системы анализа ошибок")
    print("=" * 50)
    
    # Настройка логирования
    logging.basicConfig(level=logging.INFO)
    
    # Запуск тестов
    test_ocr_module()
    test_ai_classifier()
    test_database()
    test_web_search()
    test_full_pipeline()
    
    print("\n" + "=" * 50)
    print("✅ Тестирование завершено!")
    print("\nДля запуска приложения используйте:")
    print("python run.py")

if __name__ == "__main__":
    main() 