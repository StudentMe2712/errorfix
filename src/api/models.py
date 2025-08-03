"""
Pydantic модели для API
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

class ErrorSeverity(str, Enum):
    """Уровни серьезности ошибок"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ApplicationType(str, Enum):
    """Типы приложений"""
    ONEC = "1c"
    WINDOWS = "windows"
    OFFICE = "office"
    BROWSER = "browser"
    ANTIVIRUS = "antivirus"
    OTHER = "other"

class ErrorClassification(BaseModel):
    """Классификация ошибки"""
    application_type: ApplicationType
    category: str
    severity: ErrorSeverity
    keywords: List[str]
    suggested_actions: List[str]
    confidence: float = Field(ge=0.0, le=1.0)

class Solution(BaseModel):
    """Решение проблемы"""
    id: Optional[int] = None
    title: str
    description: str
    steps: List[str]
    source: str
    success_rate: float = Field(ge=0.0, le=1.0, default=0.0)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class OCRResult(BaseModel):
    """Результат OCR"""
    text: str
    confidence: float
    engine: str
    language: str

class ErrorAnalysis(BaseModel):
    """Анализ ошибки"""
    ocr_result: OCRResult
    classification: ErrorClassification
    solutions: List[Solution]
    web_solutions: List[Solution]
    processing_time: float
    error_codes: List[str] = []

class UploadScreenshotRequest(BaseModel):
    """Запрос на загрузку скриншота"""
    description: Optional[str] = None

class UploadScreenshotResponse(BaseModel):
    """Ответ на загрузку скриншота"""
    file_id: str
    filename: str
    size: int
    uploaded_at: datetime

class AnalyzeErrorRequest(BaseModel):
    """Запрос на анализ ошибки"""
    file_id: str
    additional_context: Optional[str] = None

class AnalyzeErrorResponse(BaseModel):
    """Ответ на анализ ошибки"""
    analysis: ErrorAnalysis
    status: str = "success"
    message: Optional[str] = None

class AddSolutionRequest(BaseModel):
    """Запрос на добавление решения"""
    title: str
    description: str
    steps: List[str]
    application_type: ApplicationType
    error_codes: List[str] = []
    keywords: List[str] = []

class AddSolutionResponse(BaseModel):
    """Ответ на добавление решения"""
    solution_id: int
    status: str = "success"
    message: str = "Решение добавлено успешно"

class FeedbackRequest(BaseModel):
    """Запрос обратной связи"""
    solution_id: int
    was_helpful: bool
    comment: Optional[str] = None

class StatisticsResponse(BaseModel):
    """Статистика системы"""
    total_errors_processed: int
    total_solutions: int
    average_processing_time: float
    most_common_errors: List[Dict[str, Any]]
    success_rate: float

class ErrorResponse(BaseModel):
    """Стандартный ответ об ошибке"""
    status: str = "error"
    message: str
    details: Optional[Dict[str, Any]] = None 