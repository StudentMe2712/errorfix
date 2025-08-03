"""
Модуль базы знаний с SQLite и векторным поиском
"""

import sqlite3
import json
import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
import os
from dataclasses import dataclass, asdict

try:
    import chromadb
    from chromadb.config import Settings
    CHROMA_AVAILABLE = True
except ImportError:
    CHROMA_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

logger = logging.getLogger(__name__)

@dataclass
class Solution:
    """Структура решения"""
    id: Optional[int]
    error_text: str
    solution_text: str
    application_type: str
    error_category: str
    source: str
    success_rate: Optional[float]
    created_at: str
    tags: List[str]
    steps: List[str]

class KnowledgeBase:
    """Класс для работы с базой знаний"""
    
    def __init__(self, db_path: str = "solutions.db", chroma_path: str = "./chroma_db"):
        self.db_path = db_path
        self.chroma_path = chroma_path
        self.vector_store = None
        
        # Инициализация базы данных
        self._init_database()
        
        # Инициализация векторного хранилища
        if CHROMA_AVAILABLE and SENTENCE_TRANSFORMERS_AVAILABLE:
            self._init_vector_store()
    
    def _init_database(self):
        """Инициализация SQLite базы данных"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Создание таблицы решений
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS solutions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        error_text TEXT NOT NULL,
                        solution_text TEXT NOT NULL,
                        application_type TEXT,
                        error_category TEXT,
                        source TEXT,
                        success_rate REAL,
                        created_at TEXT NOT NULL,
                        tags TEXT,
                        steps TEXT
                    )
                ''')
                
                # Создание индексов для быстрого поиска
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_error_text 
                    ON solutions(error_text)
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_application_type 
                    ON solutions(application_type)
                ''')
                cursor.execute('''
                    CREATE INDEX IF NOT EXISTS idx_error_category 
                    ON solutions(error_category)
                ''')
                
                conn.commit()
                logger.info("База данных инициализирована успешно")
                
        except Exception as e:
            logger.error(f"Ошибка инициализации базы данных: {e}")
    
    def _init_vector_store(self):
        """Инициализация векторного хранилища"""
        try:
            # Создание директории для ChromaDB
            os.makedirs(self.chroma_path, exist_ok=True)
            
            # Инициализация ChromaDB
            self.vector_store = chromadb.PersistentClient(
                path=self.chroma_path,
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Создание коллекции
            self.collection = self.vector_store.get_or_create_collection(
                name="solutions",
                metadata={"hnsw:space": "cosine"}
            )
            
            logger.info("Векторное хранилище инициализировано успешно")
            
        except Exception as e:
            logger.error(f"Ошибка инициализации векторного хранилища: {e}")
    
    def add_solution(self, solution: Solution) -> bool:
        """
        Добавление решения в базу знаний
        
        Args:
            solution: Объект решения
            
        Returns:
            True если добавление успешно
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    INSERT INTO solutions 
                    (error_text, solution_text, application_type, error_category, 
                     source, success_rate, created_at, tags, steps)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    solution.error_text,
                    solution.solution_text,
                    solution.application_type,
                    solution.error_category,
                    solution.source,
                    solution.success_rate,
                    solution.created_at,
                    json.dumps(solution.tags),
                    json.dumps(solution.steps)
                ))
                
                solution_id = cursor.lastrowid
                conn.commit()
                
                # Добавление в векторное хранилище
                if self.vector_store:
                    self._add_to_vector_store(solution_id, solution)
                
                logger.info(f"Решение добавлено с ID: {solution_id}")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка добавления решения: {e}")
            return False
    
    def _add_to_vector_store(self, solution_id: int, solution: Solution):
        """Добавление решения в векторное хранилище"""
        try:
            # Создание эмбеддинга для поиска
            search_text = f"{solution.error_text} {solution.application_type} {solution.error_category}"
            
            # Добавление в коллекцию
            self.collection.add(
                documents=[search_text],
                metadatas=[{
                    "solution_id": solution_id,
                    "application_type": solution.application_type,
                    "error_category": solution.error_category,
                    "source": solution.source
                }],
                ids=[str(solution_id)]
            )
            
        except Exception as e:
            logger.error(f"Ошибка добавления в векторное хранилище: {e}")
    
    def search_solutions(self, query: str, application_type: str = None, 
                        limit: int = 10) -> List[Solution]:
        """
        Поиск решений
        
        Args:
            query: Поисковый запрос
            application_type: Тип приложения для фильтрации
            limit: Максимальное количество результатов
            
        Returns:
            Список найденных решений
        """
        solutions = []
        
        # Векторный поиск (если доступен)
        if self.vector_store:
            vector_results = self._vector_search(query, application_type, limit)
            solutions.extend(vector_results)
        
        # Текстовый поиск в SQLite
        text_results = self._text_search(query, application_type, limit)
        solutions.extend(text_results)
        
        # Удаление дубликатов и сортировка по релевантности
        unique_solutions = self._deduplicate_solutions(solutions)
        return unique_solutions[:limit]
    
    def _vector_search(self, query: str, application_type: str = None, 
                      limit: int = 10) -> List[Solution]:
        """Векторный поиск"""
        try:
            # Построение запроса
            search_query = query
            if application_type:
                search_query += f" {application_type}"
            
            # Поиск в векторном хранилище
            results = self.collection.query(
                query_texts=[search_query],
                n_results=limit,
                where={"application_type": application_type} if application_type else None
            )
            
            # Получение решений из SQLite по ID
            solution_ids = [int(id) for id in results['ids'][0]]
            return self._get_solutions_by_ids(solution_ids)
            
        except Exception as e:
            logger.error(f"Ошибка векторного поиска: {e}")
            return []
    
    def _text_search(self, query: str, application_type: str = None, 
                    limit: int = 10) -> List[Solution]:
        """Текстовый поиск в SQLite"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Построение SQL запроса
                sql = '''
                    SELECT * FROM solutions 
                    WHERE error_text LIKE ? OR solution_text LIKE ?
                '''
                params = [f"%{query}%", f"%{query}%"]
                
                if application_type:
                    sql += " AND application_type = ?"
                    params.append(application_type)
                
                sql += " ORDER BY success_rate DESC LIMIT ?"
                params.append(limit)
                
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                
                return [self._row_to_solution(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Ошибка текстового поиска: {e}")
            return []
    
    def _get_solutions_by_ids(self, solution_ids: List[int]) -> List[Solution]:
        """Получение решений по ID"""
        if not solution_ids:
            return []
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                placeholders = ','.join(['?' for _ in solution_ids])
                cursor.execute(f'''
                    SELECT * FROM solutions 
                    WHERE id IN ({placeholders})
                ''', solution_ids)
                
                rows = cursor.fetchall()
                return [self._row_to_solution(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Ошибка получения решений по ID: {e}")
            return []
    
    def _row_to_solution(self, row: Tuple) -> Solution:
        """Преобразование строки БД в объект Solution"""
        return Solution(
            id=row[0],
            error_text=row[1],
            solution_text=row[2],
            application_type=row[3],
            error_category=row[4],
            source=row[5],
            success_rate=row[6],
            created_at=row[7],
            tags=json.loads(row[8]) if row[8] else [],
            steps=json.loads(row[9]) if row[9] else []
        )
    
    def _deduplicate_solutions(self, solutions: List[Solution]) -> List[Solution]:
        """Удаление дубликатов решений"""
        seen_ids = set()
        unique_solutions = []
        
        for solution in solutions:
            if solution.id not in seen_ids:
                seen_ids.add(solution.id)
                unique_solutions.append(solution)
        
        return unique_solutions
    
    def get_solution_by_id(self, solution_id: int) -> Optional[Solution]:
        """Получение решения по ID"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM solutions WHERE id = ?', (solution_id,))
                row = cursor.fetchone()
                
                if row:
                    return self._row_to_solution(row)
                return None
                
        except Exception as e:
            logger.error(f"Ошибка получения решения по ID: {e}")
            return None
    
    def update_success_rate(self, solution_id: int, success_rate: float) -> bool:
        """Обновление рейтинга успешности решения"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE solutions 
                    SET success_rate = ? 
                    WHERE id = ?
                ''', (success_rate, solution_id))
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Ошибка обновления рейтинга: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, any]:
        """Получение статистики базы знаний"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Общее количество решений
                cursor.execute('SELECT COUNT(*) FROM solutions')
                total_solutions = cursor.fetchone()[0]
                
                # Количество по типам приложений
                cursor.execute('''
                    SELECT application_type, COUNT(*) 
                    FROM solutions 
                    GROUP BY application_type
                ''')
                app_stats = dict(cursor.fetchall())
                
                # Количество по категориям ошибок
                cursor.execute('''
                    SELECT error_category, COUNT(*) 
                    FROM solutions 
                    GROUP BY error_category
                ''')
                category_stats = dict(cursor.fetchall())
                
                # Средний рейтинг успешности
                cursor.execute('SELECT AVG(success_rate) FROM solutions WHERE success_rate IS NOT NULL')
                avg_success_rate = cursor.fetchone()[0] or 0
                
                return {
                    'total_solutions': total_solutions,
                    'application_stats': app_stats,
                    'category_stats': category_stats,
                    'avg_success_rate': avg_success_rate
                }
                
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return {}
    
    def export_solutions(self, filepath: str) -> bool:
        """Экспорт решений в JSON файл"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM solutions')
                rows = cursor.fetchall()
                
                solutions = [self._row_to_solution(row) for row in rows]
                solutions_dict = [asdict(solution) for solution in solutions]
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(solutions_dict, f, ensure_ascii=False, indent=2)
                
                logger.info(f"Экспортировано {len(solutions)} решений в {filepath}")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка экспорта: {e}")
            return False
    
    def import_solutions(self, filepath: str) -> bool:
        """Импорт решений из JSON файла"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                solutions_data = json.load(f)
            
            for solution_data in solutions_data:
                solution = Solution(
                    id=None,  # Будет установлен автоматически
                    error_text=solution_data['error_text'],
                    solution_text=solution_data['solution_text'],
                    application_type=solution_data['application_type'],
                    error_category=solution_data['error_category'],
                    source=solution_data['source'],
                    success_rate=solution_data['success_rate'],
                    created_at=datetime.now().isoformat(),
                    tags=solution_data.get('tags', []),
                    steps=solution_data.get('steps', [])
                )
                self.add_solution(solution)
            
            logger.info(f"Импортировано {len(solutions_data)} решений из {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка импорта: {e}")
            return False 