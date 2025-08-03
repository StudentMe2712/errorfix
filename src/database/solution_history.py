"""
Модуль для ведения истории решенных проблем
"""

import sqlite3
import logging
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path
import json

logger = logging.getLogger(__name__)

class SolutionHistory:
    """Класс для ведения истории решенных проблем"""
    
    def __init__(self, db_path: str = "data/solution_history.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Инициализация базы данных истории"""
        try:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Таблица истории решений
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS solution_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        error_text TEXT NOT NULL,
                        error_type TEXT,
                        application_type TEXT,
                        solution_id INTEGER,
                        solution_title TEXT,
                        solution_description TEXT,
                        was_helpful BOOLEAN,
                        processing_time REAL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Таблица пользовательских заметок
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS user_notes (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        history_id INTEGER,
                        note_text TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (history_id) REFERENCES solution_history (id)
                    )
                """)
                
                # Таблица тегов
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS history_tags (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        history_id INTEGER,
                        tag_name TEXT NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (history_id) REFERENCES solution_history (id)
                    )
                """)
                
                # Индексы для производительности
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_error_type ON solution_history (error_type)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_application_type ON solution_history (application_type)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON solution_history (created_at)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_was_helpful ON solution_history (was_helpful)")
                
                conn.commit()
                logger.info("База данных истории решений инициализирована")
                
        except Exception as e:
            logger.error(f"Ошибка инициализации базы данных истории: {e}")
    
    def add_solution_record(self, error_text: str, error_type: str, application_type: str,
                           solution_id: Optional[int] = None, solution_title: str = "",
                           solution_description: str = "", processing_time: float = 0.0) -> int:
        """
        Добавление записи о решении проблемы
        
        Args:
            error_text: Текст ошибки
            error_type: Тип ошибки
            application_type: Тип приложения
            solution_id: ID решения из базы знаний
            solution_title: Заголовок решения
            solution_description: Описание решения
            processing_time: Время обработки
            
        Returns:
            ID созданной записи
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO solution_history 
                    (error_text, error_type, application_type, solution_id, 
                     solution_title, solution_description, processing_time)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (error_text, error_type, application_type, solution_id,
                      solution_title, solution_description, processing_time))
                
                record_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"Добавлена запись в историю: ID {record_id}")
                return record_id
                
        except Exception as e:
            logger.error(f"Ошибка добавления записи в историю: {e}")
            return -1
    
    def update_solution_feedback(self, record_id: int, was_helpful: bool) -> bool:
        """
        Обновление обратной связи по решению
        
        Args:
            record_id: ID записи
            was_helpful: Было ли решение полезным
            
        Returns:
            True если успешно
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    UPDATE solution_history 
                    SET was_helpful = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (was_helpful, record_id))
                
                conn.commit()
                logger.info(f"Обновлена обратная связь для записи {record_id}")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка обновления обратной связи: {e}")
            return False
    
    def add_user_note(self, history_id: int, note_text: str) -> bool:
        """
        Добавление пользовательской заметки
        
        Args:
            history_id: ID записи истории
            note_text: Текст заметки
            
        Returns:
            True если успешно
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO user_notes (history_id, note_text)
                    VALUES (?, ?)
                """, (history_id, note_text))
                
                conn.commit()
                logger.info(f"Добавлена заметка для записи {history_id}")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка добавления заметки: {e}")
            return False
    
    def add_tag(self, history_id: int, tag_name: str) -> bool:
        """
        Добавление тега к записи
        
        Args:
            history_id: ID записи истории
            tag_name: Название тега
            
        Returns:
            True если успешно
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO history_tags (history_id, tag_name)
                    VALUES (?, ?)
                """, (history_id, tag_name))
                
                conn.commit()
                logger.info(f"Добавлен тег '{tag_name}' для записи {history_id}")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка добавления тега: {e}")
            return False
    
    def get_history(self, limit: int = 50, offset: int = 0, 
                   error_type: str = None, application_type: str = None,
                   was_helpful: bool = None) -> List[Dict]:
        """
        Получение истории решений
        
        Args:
            limit: Количество записей
            offset: Смещение
            error_type: Фильтр по типу ошибки
            application_type: Фильтр по типу приложения
            was_helpful: Фильтр по полезности
            
        Returns:
            Список записей истории
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                query = """
                    SELECT h.*, 
                           GROUP_CONCAT(DISTINCT n.note_text) as notes,
                           GROUP_CONCAT(DISTINCT t.tag_name) as tags
                    FROM solution_history h
                    LEFT JOIN user_notes n ON h.id = n.history_id
                    LEFT JOIN history_tags t ON h.id = t.history_id
                """
                
                conditions = []
                params = []
                
                if error_type:
                    conditions.append("h.error_type = ?")
                    params.append(error_type)
                
                if application_type:
                    conditions.append("h.application_type = ?")
                    params.append(application_type)
                
                if was_helpful is not None:
                    conditions.append("h.was_helpful = ?")
                    params.append(was_helpful)
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
                
                query += " GROUP BY h.id ORDER BY h.created_at DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Ошибка получения истории: {e}")
            return []
    
    def get_statistics(self) -> Dict:
        """
        Получение статистики истории
        
        Returns:
            Статистика истории
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Общее количество записей
                cursor.execute("SELECT COUNT(*) FROM solution_history")
                total_records = cursor.fetchone()[0]
                
                # Записи по типам ошибок
                cursor.execute("""
                    SELECT error_type, COUNT(*) 
                    FROM solution_history 
                    GROUP BY error_type
                """)
                error_types = dict(cursor.fetchall())
                
                # Записи по типам приложений
                cursor.execute("""
                    SELECT application_type, COUNT(*) 
                    FROM solution_history 
                    GROUP BY application_type
                """)
                application_types = dict(cursor.fetchall())
                
                # Полезные решения
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM solution_history 
                    WHERE was_helpful = 1
                """)
                helpful_solutions = cursor.fetchone()[0]
                
                # Среднее время обработки
                cursor.execute("""
                    SELECT AVG(processing_time) 
                    FROM solution_history 
                    WHERE processing_time > 0
                """)
                avg_processing_time = cursor.fetchone()[0] or 0
                
                return {
                    'total_records': total_records,
                    'error_types': error_types,
                    'application_types': application_types,
                    'helpful_solutions': helpful_solutions,
                    'avg_processing_time': avg_processing_time,
                    'success_rate': (helpful_solutions / total_records * 100) if total_records > 0 else 0
                }
                
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return {}
    
    def search_history(self, query: str) -> List[Dict]:
        """
        Поиск в истории
        
        Args:
            query: Поисковый запрос
            
        Returns:
            Список найденных записей
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                search_query = f"%{query}%"
                
                cursor.execute("""
                    SELECT h.*, 
                           GROUP_CONCAT(DISTINCT n.note_text) as notes,
                           GROUP_CONCAT(DISTINCT t.tag_name) as tags
                    FROM solution_history h
                    LEFT JOIN user_notes n ON h.id = n.history_id
                    LEFT JOIN history_tags t ON h.id = t.history_id
                    WHERE h.error_text LIKE ? 
                       OR h.solution_title LIKE ? 
                       OR h.solution_description LIKE ?
                       OR n.note_text LIKE ?
                       OR t.tag_name LIKE ?
                    GROUP BY h.id
                    ORDER BY h.created_at DESC
                """, (search_query, search_query, search_query, search_query, search_query))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Ошибка поиска в истории: {e}")
            return []
    
    def export_history(self, format: str = 'json') -> str:
        """
        Экспорт истории
        
        Args:
            format: Формат экспорта ('json' или 'csv')
            
        Returns:
            Путь к экспортированному файлу
        """
        try:
            history = self.get_history(limit=10000)  # Все записи
            
            if format == 'json':
                export_path = f"data/history_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(export_path, 'w', encoding='utf-8') as f:
                    json.dump(history, f, ensure_ascii=False, indent=2)
            
            elif format == 'csv':
                import csv
                export_path = f"data/history_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                with open(export_path, 'w', newline='', encoding='utf-8') as f:
                    if history:
                        writer = csv.DictWriter(f, fieldnames=history[0].keys())
                        writer.writeheader()
                        writer.writerows(history)
            
            logger.info(f"История экспортирована в {export_path}")
            return export_path
            
        except Exception as e:
            logger.error(f"Ошибка экспорта истории: {e}")
            return ""
    
    def clear_history(self, older_than_days: int = None) -> bool:
        """
        Очистка истории
        
        Args:
            older_than_days: Удалить записи старше указанного количества дней
            
        Returns:
            True если успешно
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if older_than_days:
                    cursor.execute("""
                        DELETE FROM solution_history 
                        WHERE created_at < datetime('now', '-{} days')
                    """.format(older_than_days))
                else:
                    cursor.execute("DELETE FROM solution_history")
                    cursor.execute("DELETE FROM user_notes")
                    cursor.execute("DELETE FROM history_tags")
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                logger.info(f"Удалено {deleted_count} записей из истории")
                return True
                
        except Exception as e:
            logger.error(f"Ошибка очистки истории: {e}")
            return False 