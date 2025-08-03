"""
Streamlit приложение для анализа скриншотов ошибок
"""

import streamlit as st
import cv2
import numpy as np
from PIL import Image
import io
import logging
from datetime import datetime
import os

# Импорт наших модулей
from ocr.image_preprocessor import ImagePreprocessor
from ocr.text_extractor import TextExtractor
from ai.error_classifier import ErrorClassifier
from database.knowledge_base import KnowledgeBase, Solution

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация компонентов
@st.cache_resource
def init_components():
    """Инициализация компонентов системы"""
    preprocessor = ImagePreprocessor()
    extractor = TextExtractor()
    classifier = ErrorClassifier(llm_provider="groq")  # или "ollama"
    knowledge_base = KnowledgeBase()
    return preprocessor, extractor, classifier, knowledge_base

def main():
    """Основная функция приложения"""
    st.set_page_config(
        page_title="Умный парсер ошибок",
        page_icon="🔍",
        layout="wide"
    )
    
    st.title("🔍 Умный парсер скриншотов ошибок")
    st.markdown("Загрузите скриншот ошибки и получите автоматический анализ и решения")
    
    # Инициализация компонентов
    preprocessor, extractor, classifier, knowledge_base = init_components()
    
    # Боковая панель с настройками
    with st.sidebar:
        st.header("⚙️ Настройки")
        
        # Выбор LLM провайдера
        llm_provider = st.selectbox(
            "LLM провайдер",
            ["groq", "ollama", "openai"],
            help="Выберите провайдера для AI анализа"
        )
        
        # Настройки OCR
        use_multiple_engines = st.checkbox(
            "Использовать несколько OCR движков",
            value=True,
            help="Улучшает точность распознавания"
        )
        
        # Показать статистику
        if st.button("📊 Показать статистику"):
            show_statistics(knowledge_base)
    
    # Основная область
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📸 Загрузка скриншота")
        
        # Загрузка файла
        uploaded_file = st.file_uploader(
            "Выберите изображение с ошибкой",
            type=['png', 'jpg', 'jpeg', 'bmp'],
            help="Поддерживаются форматы: PNG, JPG, JPEG, BMP"
        )
        
        if uploaded_file is not None:
            # Отображение загруженного изображения
            image = Image.open(uploaded_file)
            st.image(image, caption="Загруженное изображение", use_column_width=True)
            
            # Конвертация в numpy array
            image_array = np.array(image)
            
            # Обработка изображения
            if st.button("🔍 Анализировать ошибку"):
                with st.spinner("Обрабатываю изображение..."):
                    process_error_screenshot(
                        image_array, preprocessor, extractor, 
                        classifier, knowledge_base, use_multiple_engines
                    )
    
    with col2:
        st.header("📋 Результаты анализа")
        
        # Область для отображения результатов
        if 'analysis_results' in st.session_state:
            display_results(st.session_state.analysis_results)
        
        # Область для отображения решений
        if 'solutions' in st.session_state:
            display_solutions(st.session_state.solutions, knowledge_base)

def process_error_screenshot(image_array, preprocessor, extractor, classifier, knowledge_base, use_multiple_engines):
    """Обработка скриншота ошибки"""
    try:
        # 1. Предобработка изображения
        st.info("🔄 Предобработка изображения...")
        processed_image = preprocessor.preprocess_image(image_array)
        
        # 2. Извлечение текста
        st.info("📝 Извлечение текста...")
        ocr_results = extractor.extract_text(processed_image, use_multiple_engines)
        
        if not ocr_results:
            st.error("❌ Не удалось извлечь текст из изображения")
            return
        
        # Выбор лучшего результата
        best_result = extractor.select_best_result(ocr_results)
        if not best_result:
            st.error("❌ Не удалось выбрать лучший результат OCR")
            return
        
        # Очистка текста
        cleaned_text = extractor.clean_text(best_result.text)
        
        # 3. Извлечение структурированной информации
        error_info = extractor.extract_structured_error_info(cleaned_text)
        
        # 4. Классификация ошибки
        st.info("🤖 Анализ ошибки...")
        classification = classifier.classify_error(cleaned_text, error_info)
        
        # 5. Поиск решений
        st.info("🔍 Поиск решений...")
        solutions = knowledge_base.search_solutions(
            cleaned_text, 
            classification.application_type,
            limit=5
        )
        
        # Сохранение результатов в session state
        st.session_state.analysis_results = {
            'ocr_result': best_result,
            'cleaned_text': cleaned_text,
            'error_info': error_info,
            'classification': classification
        }
        st.session_state.solutions = solutions
        
        st.success("✅ Анализ завершен!")
        
    except Exception as e:
        st.error(f"❌ Ошибка при обработке: {e}")
        logger.error(f"Ошибка обработки скриншота: {e}")

def display_results(results):
    """Отображение результатов анализа"""
    st.subheader("📊 Результаты анализа")
    
    # OCR результат
    with st.expander("📝 Распознанный текст", expanded=True):
        st.text_area(
            "Текст ошибки:",
            results['cleaned_text'],
            height=150,
            help="Распознанный текст с изображения"
        )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Уверенность OCR", f"{results['ocr_result'].confidence:.1f}%")
        with col2:
            st.metric("Движок OCR", results['ocr_result'].engine)
        with col3:
            st.metric("Язык", results['ocr_result'].language)
    
    # Структурированная информация
    with st.expander("🔍 Структурированная информация"):
        error_info = results['error_info']
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Код ошибки:**", error_info.get('error_code', 'Не найден'))
            st.write("**Приложение:**", error_info.get('application', 'Не определено'))
        
        with col2:
            st.write("**Сообщение:**", error_info.get('error_message', 'Не найдено'))
            st.write("**Временная метка:**", error_info.get('timestamp', 'Не найдена'))
    
    # Классификация
    with st.expander("🤖 AI классификация"):
        classification = results['classification']
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Тип приложения", classification.application_type.upper())
        with col2:
            st.metric("Категория", classification.error_category.upper())
        with col3:
            st.metric("Серьезность", classification.severity.upper())
        
        st.write("**Ключевые слова:**", ", ".join(classification.keywords))
        st.write("**Уверенность:**", f"{classification.confidence:.1f}%")
        
        if classification.suggested_actions:
            st.write("**Предлагаемые действия:**")
            for i, action in enumerate(classification.suggested_actions, 1):
                st.write(f"{i}. {action}")

def display_solutions(solutions, knowledge_base):
    """Отображение найденных решений"""
    st.subheader("💡 Найденные решения")
    
    if not solutions:
        st.warning("⚠️ Решения не найдены в базе знаний")
        
        # Предложение добавить решение
        with st.expander("➕ Добавить новое решение"):
            add_solution_form(knowledge_base)
        return
    
    # Отображение решений
    for i, solution in enumerate(solutions, 1):
        with st.expander(f"Решение #{i}: {solution.error_category}", expanded=i==1):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write("**Описание решения:**")
                st.write(solution.solution_text)
                
                if solution.steps:
                    st.write("**Пошаговые инструкции:**")
                    for j, step in enumerate(solution.steps, 1):
                        st.write(f"{j}. {step}")
                
                if solution.tags:
                    st.write("**Теги:**", ", ".join(solution.tags))
            
            with col2:
                st.metric("Источник", solution.source)
                if solution.success_rate:
                    st.metric("Успешность", f"{solution.success_rate:.1f}%")
                st.metric("Дата", solution.created_at[:10])
                
                # Кнопка обратной связи
                if st.button(f"👍 Помогло", key=f"helpful_{i}"):
                    update_success_rate(solution.id, solution.success_rate + 10, knowledge_base)
                    st.success("Спасибо за обратную связь!")
                
                if st.button(f"👎 Не помогло", key=f"not_helpful_{i}"):
                    update_success_rate(solution.id, max(0, solution.success_rate - 10), knowledge_base)
                    st.error("Спасибо за обратную связь!")

def add_solution_form(knowledge_base):
    """Форма добавления нового решения"""
    with st.form("add_solution"):
        st.write("Добавьте новое решение в базу знаний")
        
        error_text = st.text_area("Текст ошибки", value=st.session_state.get('cleaned_text', ''))
        solution_text = st.text_area("Описание решения")
        application_type = st.selectbox("Тип приложения", ["1c", "windows", "office", "browser", "other"])
        error_category = st.selectbox("Категория ошибки", ["sql", "config", "rights", "system", "connection", "other"])
        source = st.text_input("Источник решения", value="Пользователь")
        success_rate = st.slider("Начальный рейтинг успешности", 0, 100, 50)
        
        steps = st.text_area("Пошаговые инструкции (каждый шаг с новой строки)")
        tags = st.text_input("Теги (через запятую)")
        
        if st.form_submit_button("Добавить решение"):
            if error_text and solution_text:
                solution = Solution(
                    id=None,
                    error_text=error_text,
                    solution_text=solution_text,
                    application_type=application_type,
                    error_category=error_category,
                    source=source,
                    success_rate=success_rate,
                    created_at=datetime.now().isoformat(),
                    tags=[tag.strip() for tag in tags.split(",") if tag.strip()],
                    steps=[step.strip() for step in steps.split("\n") if step.strip()]
                )
                
                if knowledge_base.add_solution(solution):
                    st.success("✅ Решение добавлено в базу знаний!")
                else:
                    st.error("❌ Ошибка при добавлении решения")
            else:
                st.error("❌ Заполните обязательные поля")

def update_success_rate(solution_id, new_rate, knowledge_base):
    """Обновление рейтинга успешности"""
    try:
        knowledge_base.update_success_rate(solution_id, new_rate)
    except Exception as e:
        logger.error(f"Ошибка обновления рейтинга: {e}")

def show_statistics(knowledge_base):
    """Отображение статистики базы знаний"""
    stats = knowledge_base.get_statistics()
    
    st.subheader("📊 Статистика базы знаний")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Всего решений", stats.get('total_solutions', 0))
    with col2:
        st.metric("Средний рейтинг", f"{stats.get('avg_success_rate', 0):.1f}%")
    with col3:
        st.metric("Типы приложений", len(stats.get('application_stats', {})))
    
    # Детальная статистика
    with st.expander("📈 Детальная статистика"):
        if stats.get('application_stats'):
            st.write("**По типам приложений:**")
            for app, count in stats['application_stats'].items():
                st.write(f"- {app}: {count}")
        
        if stats.get('category_stats'):
            st.write("**По категориям ошибок:**")
            for category, count in stats['category_stats'].items():
                st.write(f"- {category}: {count}")

if __name__ == "__main__":
    main() 