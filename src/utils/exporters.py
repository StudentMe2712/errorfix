"""
Модуль для экспорта решений в различные системы управления знаниями
"""

import json
import logging
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime
import re

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    logging.warning("requests не установлен. Экспорт в Notion недоступен.")

logger = logging.getLogger(__name__)

class NotionExporter:
    """Экспортер для Notion"""
    
    def __init__(self, api_key: str = None, database_id: str = None):
        self.api_key = api_key
        self.database_id = database_id
        self.base_url = "https://api.notion.com/v1"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Notion-Version": "2022-06-28"
        } if api_key else {}
    
    def export_solution(self, solution: Dict, error_text: str = "") -> bool:
        """
        Экспорт решения в Notion
        
        Args:
            solution: Данные решения
            error_text: Текст ошибки
            
        Returns:
            True если успешно
        """
        if not self.api_key or not self.database_id:
            logger.error("Не настроены API ключ или ID базы данных Notion")
            return False
        
        try:
            # Создание страницы в Notion
            page_data = {
                "parent": {"database_id": self.database_id},
                "properties": {
                    "Title": {
                        "title": [
                            {
                                "text": {
                                    "content": solution.get('title', 'Решение ошибки')
                                }
                            }
                        ]
                    },
                    "Error Type": {
                        "select": {
                            "name": solution.get('application_type', 'Unknown')
                        }
                    },
                    "Status": {
                        "select": {
                            "name": "Active"
                        }
                    }
                },
                "children": [
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": "Описание ошибки"
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": error_text or "Ошибка не указана"
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "object": "block",
                        "type": "heading_2",
                        "heading_2": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": "Решение"
                                    }
                                }
                            ]
                        }
                    },
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": solution.get('description', '')
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
            
            # Добавление шагов решения
            steps = solution.get('steps', [])
            if steps:
                page_data["children"].append({
                    "object": "block",
                    "type": "heading_2",
                    "heading_2": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": "Пошаговое решение"
                                }
                            }
                        ]
                    }
                })
                
                for i, step in enumerate(steps, 1):
                    page_data["children"].append({
                        "object": "block",
                        "type": "numbered_list_item",
                        "numbered_list_item": {
                            "rich_text": [
                                {
                                    "type": "text",
                                    "text": {
                                        "content": f"{i}. {step}"
                                    }
                                }
                            ]
                        }
                    })
            
            # Отправка запроса
            response = requests.post(
                f"{self.base_url}/pages",
                headers=self.headers,
                json=page_data
            )
            
            if response.status_code == 200:
                logger.info(f"Решение экспортировано в Notion: {response.json().get('id')}")
                return True
            else:
                logger.error(f"Ошибка экспорта в Notion: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"Ошибка экспорта в Notion: {e}")
            return False
    
    def export_multiple_solutions(self, solutions: List[Dict], error_text: str = "") -> Dict:
        """
        Экспорт нескольких решений
        
        Args:
            solutions: Список решений
            error_text: Текст ошибки
            
        Returns:
            Статистика экспорта
        """
        results = {
            'total': len(solutions),
            'success': 0,
            'failed': 0,
            'errors': []
        }
        
        for solution in solutions:
            try:
                if self.export_solution(solution, error_text):
                    results['success'] += 1
                else:
                    results['failed'] += 1
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(str(e))
        
        return results

class ObsidianExporter:
    """Экспортер для Obsidian"""
    
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.vault_path.mkdir(parents=True, exist_ok=True)
    
    def export_solution(self, solution: Dict, error_text: str = "") -> str:
        """
        Экспорт решения в Obsidian
        
        Args:
            solution: Данные решения
            error_text: Текст ошибки
            
        Returns:
            Путь к созданному файлу
        """
        try:
            # Создание имени файла
            title = solution.get('title', 'Решение ошибки')
            safe_title = re.sub(r'[^\w\s-]', '', title)
            safe_title = re.sub(r'[-\s]+', '-', safe_title)
            
            filename = f"{safe_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            file_path = self.vault_path / filename
            
            # Создание содержимого файла
            content = self._create_markdown_content(solution, error_text)
            
            # Запись файла
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Решение экспортировано в Obsidian: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"Ошибка экспорта в Obsidian: {e}")
            return ""
    
    def _create_markdown_content(self, solution: Dict, error_text: str) -> str:
        """Создание содержимого Markdown файла"""
        content = []
        
        # Заголовок
        content.append(f"# {solution.get('title', 'Решение ошибки')}")
        content.append("")
        
        # Метаданные
        content.append("## Метаданные")
        content.append(f"- **Тип приложения:** {solution.get('application_type', 'Unknown')}")
        content.append(f"- **Дата создания:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        content.append(f"- **Источник:** {solution.get('source', 'Unknown')}")
        content.append("")
        
        # Описание ошибки
        if error_text:
            content.append("## Описание ошибки")
            content.append(f"```")
            content.append(error_text)
            content.append("```")
            content.append("")
        
        # Описание решения
        content.append("## Описание решения")
        content.append(solution.get('description', ''))
        content.append("")
        
        # Пошаговое решение
        steps = solution.get('steps', [])
        if steps:
            content.append("## Пошаговое решение")
            for i, step in enumerate(steps, 1):
                content.append(f"{i}. {step}")
            content.append("")
        
        # Коды ошибок
        error_codes = solution.get('error_codes', [])
        if error_codes:
            content.append("## Коды ошибок")
            for code in error_codes:
                content.append(f"- `{code}`")
            content.append("")
        
        # Ключевые слова
        keywords = solution.get('keywords', [])
        if keywords:
            content.append("## Ключевые слова")
            for keyword in keywords:
                content.append(f"- `{keyword}`")
            content.append("")
        
        # Теги
        content.append("## Теги")
        content.append(f"- #ошибка")
        content.append(f"- #{solution.get('application_type', 'unknown').lower()}")
        content.append(f"- #решение")
        content.append("")
        
        return "\n".join(content)
    
    def export_multiple_solutions(self, solutions: List[Dict], error_text: str = "") -> Dict:
        """
        Экспорт нескольких решений
        
        Args:
            solutions: Список решений
            error_text: Текст ошибки
            
        Returns:
            Статистика экспорта
        """
        results = {
            'total': len(solutions),
            'success': 0,
            'failed': 0,
            'files': [],
            'errors': []
        }
        
        for solution in solutions:
            try:
                file_path = self.export_solution(solution, error_text)
                if file_path:
                    results['success'] += 1
                    results['files'].append(file_path)
                else:
                    results['failed'] += 1
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(str(e))
        
        return results
    
    def create_index_file(self, solutions: List[Dict]) -> str:
        """
        Создание индексного файла со всеми решениями
        
        Args:
            solutions: Список решений
            
        Returns:
            Путь к индексному файлу
        """
        try:
            index_path = self.vault_path / "Решения ошибок.md"
            
            content = []
            content.append("# Решения ошибок")
            content.append("")
            content.append(f"*Создано: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
            content.append("")
            
            # Группировка по типам приложений
            by_type = {}
            for solution in solutions:
                app_type = solution.get('application_type', 'Unknown')
                if app_type not in by_type:
                    by_type[app_type] = []
                by_type[app_type].append(solution)
            
            for app_type, type_solutions in by_type.items():
                content.append(f"## {app_type}")
                content.append("")
                
                for solution in type_solutions:
                    title = solution.get('title', 'Решение ошибки')
                    safe_title = re.sub(r'[^\w\s-]', '', title)
                    safe_title = re.sub(r'[-\s]+', '-', safe_title)
                    
                    content.append(f"- [[{safe_title}]] - {solution.get('description', '')[:100]}...")
                
                content.append("")
            
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(content))
            
            logger.info(f"Индексный файл создан: {index_path}")
            return str(index_path)
            
        except Exception as e:
            logger.error(f"Ошибка создания индексного файла: {e}")
            return ""

class ExportManager:
    """Менеджер экспорта"""
    
    def __init__(self, notion_api_key: str = None, notion_database_id: str = None,
                 obsidian_vault_path: str = None):
        self.notion_exporter = None
        self.obsidian_exporter = None
        
        if notion_api_key and notion_database_id:
            self.notion_exporter = NotionExporter(notion_api_key, notion_database_id)
        
        if obsidian_vault_path:
            self.obsidian_exporter = ObsidianExporter(obsidian_vault_path)
    
    def export_to_notion(self, solution: Dict, error_text: str = "") -> bool:
        """Экспорт в Notion"""
        if not self.notion_exporter:
            logger.error("Notion экспортер не настроен")
            return False
        
        return self.notion_exporter.export_solution(solution, error_text)
    
    def export_to_obsidian(self, solution: Dict, error_text: str = "") -> str:
        """Экспорт в Obsidian"""
        if not self.obsidian_exporter:
            logger.error("Obsidian экспортер не настроен")
            return ""
        
        return self.obsidian_exporter.export_solution(solution, error_text)
    
    def export_to_all(self, solution: Dict, error_text: str = "") -> Dict:
        """Экспорт во все настроенные системы"""
        results = {
            'notion': False,
            'obsidian': "",
            'errors': []
        }
        
        # Экспорт в Notion
        if self.notion_exporter:
            try:
                results['notion'] = self.notion_exporter.export_solution(solution, error_text)
            except Exception as e:
                results['errors'].append(f"Notion: {e}")
        
        # Экспорт в Obsidian
        if self.obsidian_exporter:
            try:
                results['obsidian'] = self.obsidian_exporter.export_solution(solution, error_text)
            except Exception as e:
                results['errors'].append(f"Obsidian: {e}")
        
        return results
    
    def get_export_status(self) -> Dict:
        """Получение статуса экспортеров"""
        return {
            'notion_available': self.notion_exporter is not None,
            'obsidian_available': self.obsidian_exporter is not None,
            'obsidian_path': str(self.obsidian_exporter.vault_path) if self.obsidian_exporter else None
        } 