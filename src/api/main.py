"""
FastAPI приложение для парсера ошибок
"""

import os
import uuid
import time
from datetime import datetime
from pathlib import Path
from typing import List

import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from config import Config
from src.ocr.image_preprocessor import ImagePreprocessor
from src.ocr.text_extractor import TextExtractor
from src.ai.error_classifier import ErrorClassifier
from src.database.knowledge_base import KnowledgeBase
from src.search.web_search import WebSearch
from src.api.models import (
    UploadScreenshotResponse, AnalyzeErrorResponse, AddSolutionRequest,
    AddSolutionResponse, FeedbackRequest, StatisticsResponse, ErrorResponse
)

# Инициализация логгера
from loguru import logger
logger.add(Config.LOG_FILE, rotation="1 day", retention="7 days")

app = FastAPI(
    title="Error Screenshot Parser API",
    description="API для анализа скриншотов ошибок и поиска решений",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Инициализация компонентов
preprocessor = ImagePreprocessor()
extractor = TextExtractor()
classifier = ErrorClassifier(llm_provider=Config.LLM_PROVIDER)
knowledge_base = KnowledgeBase()
web_search = WebSearch()

@app.on_event("startup")
async def startup_event():
    """Инициализация при запуске"""
    logger.info("Запуск Error Screenshot Parser API")
    
    # Валидация конфигурации
    errors = Config.validate_config()
    if errors:
        logger.error(f"Ошибки конфигурации: {errors}")
        raise RuntimeError(f"Ошибки конфигурации: {errors}")
    
    logger.info("API готов к работе")

@app.post("/api/upload-screenshot", response_model=UploadScreenshotResponse)
async def upload_screenshot(file: UploadFile = File(...)):
    """Загрузка скриншота ошибки"""
    try:
        # Проверка расширения файла
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in Config.ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Неподдерживаемый формат файла. Разрешены: {Config.ALLOWED_EXTENSIONS}"
            )
        
        # Проверка размера файла
        if file.size > Config.MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"Файл слишком большой. Максимальный размер: {Config.MAX_FILE_SIZE // (1024*1024)}MB"
            )
        
        # Генерация уникального ID файла
        file_id = str(uuid.uuid4())
        filename = f"{file_id}{file_ext}"
        file_path = Config.UPLOADS_DIR / filename
        
        # Сохранение файла
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        
        logger.info(f"Файл загружен: {filename}, размер: {len(content)} байт")
        
        return UploadScreenshotResponse(
            file_id=file_id,
            filename=filename,
            size=len(content),
            uploaded_at=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Ошибка загрузки файла: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze-error", response_model=AnalyzeErrorResponse)
async def analyze_error(file_id: str, additional_context: str = None):
    """Анализ ошибки на скриншоте"""
    try:
        start_time = time.time()
        
        # Поиск файла
        file_path = None
        for ext in Config.ALLOWED_EXTENSIONS:
            potential_path = Config.UPLOADS_DIR / f"{file_id}{ext}"
            if potential_path.exists():
                file_path = potential_path
                break
        
        if not file_path:
            raise HTTPException(status_code=404, detail="Файл не найден")
        
        logger.info(f"Анализ ошибки для файла: {file_path}")
        
        # OCR обработка
        import cv2
        import numpy as np
        from PIL import Image
        
        image = cv2.imread(str(file_path))
        if image is None:
            raise HTTPException(status_code=400, detail="Не удалось загрузить изображение")
        
        # Предобработка
        processed_image = preprocessor.preprocess_image(image)
        
        # Извлечение текста
        ocr_results = extractor.extract_text(processed_image)
        if not ocr_results:
            raise HTTPException(status_code=400, detail="Не удалось распознать текст на изображении")
        
        best_result = extractor.select_best_result(ocr_results)
        
        # Классификация ошибки
        error_info = extractor.extract_structured_error_info(best_result.text)
        classification = classifier.classify_error(best_result.text, error_info)
        
        # Поиск решений
        local_solutions = knowledge_base.search_solutions(
            best_result.text, 
            limit=5
        )
        
        web_solutions = web_search.search_solutions(best_result.text)
        
        processing_time = time.time() - start_time
        
        logger.info(f"Анализ завершен за {processing_time:.2f} секунд")
        
        return AnalyzeErrorResponse(
            analysis={
                "ocr_result": {
                    "text": best_result.text,
                    "confidence": best_result.confidence,
                    "engine": best_result.engine,
                    "language": "rus+eng"
                },
                "classification": classification,
                "solutions": local_solutions,
                "web_solutions": web_solutions,
                "processing_time": processing_time,
                "error_codes": error_info.get("error_codes", [])
            }
        )
        
    except Exception as e:
        logger.error(f"Ошибка анализа: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/solutions/{error_id}")
async def get_solutions(error_id: str):
    """Получение решений для конкретной ошибки"""
    try:
        # Здесь можно добавить кеширование результатов
        solutions = knowledge_base.search_solutions(error_id, limit=10)
        return {"solutions": solutions}
    except Exception as e:
        logger.error(f"Ошибка получения решений: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/solutions", response_model=AddSolutionResponse)
async def add_solution(request: AddSolutionRequest):
    """Добавление нового решения"""
    try:
        from src.database.knowledge_base import Solution
        
        solution = Solution(
            title=request.title,
            description=request.description,
            steps=request.steps,
            application_type=request.application_type.value,
            error_codes=request.error_codes,
            keywords=request.keywords,
            source="user",
            success_rate=0.0
        )
        
        solution_id = knowledge_base.add_solution(solution)
        
        logger.info(f"Добавлено новое решение: {solution_id}")
        
        return AddSolutionResponse(solution_id=solution_id)
        
    except Exception as e:
        logger.error(f"Ошибка добавления решения: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/feedback")
async def submit_feedback(request: FeedbackRequest):
    """Отправка обратной связи"""
    try:
        knowledge_base.update_success_rate(
            request.solution_id, 
            request.was_helpful
        )
        
        logger.info(f"Получена обратная связь для решения {request.solution_id}")
        
        return {"status": "success", "message": "Обратная связь учтена"}
        
    except Exception as e:
        logger.error(f"Ошибка обработки обратной связи: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/statistics", response_model=StatisticsResponse)
async def get_statistics():
    """Получение статистики системы"""
    try:
        stats = knowledge_base.get_statistics()
        
        return StatisticsResponse(
            total_errors_processed=stats.get("total_errors", 0),
            total_solutions=stats.get("total_solutions", 0),
            average_processing_time=stats.get("avg_processing_time", 0.0),
            most_common_errors=stats.get("common_errors", []),
            success_rate=stats.get("success_rate", 0.0)
        )
        
    except Exception as e:
        logger.error(f"Ошибка получения статистики: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health_check():
    """Проверка состояния API"""
    return {"status": "healthy", "timestamp": datetime.now()}

if __name__ == "__main__":
    uvicorn.run(
        "src.api.main:app",
        host=Config.API_HOST,
        port=Config.API_PORT,
        reload=Config.API_DEBUG
    ) 