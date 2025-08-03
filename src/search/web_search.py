"""
Модуль веб-поиска решений в интернете
"""

import requests
import logging
from typing import List, Dict, Optional
from urllib.parse import quote_plus
import time
import re
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class WebSearch:
    """Класс для поиска решений в интернете"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Источники для поиска
        self.search_sources = {
            '1c': [
                'https://forum.1c.ru',
                'https://infostart.ru',
                'https://habr.com/ru/hub/1c/'
            ],
            'windows': [
                'https://answers.microsoft.com/ru-ru',
                'https://superuser.com',
                'https://stackoverflow.com'
            ],
            'office': [
                'https://answers.microsoft.com/ru-ru/office',
                'https://stackoverflow.com'
            ],
            'browser': [
                'https://stackoverflow.com',
                'https://superuser.com'
            ]
        }
    
    def search_solutions(self, error_text: str, application_type: str = None, 
                        max_results: int = 5) -> List[Dict]:
        """
        Поиск решений в интернете
        
        Args:
            error_text: Текст ошибки
            application_type: Тип приложения
            max_results: Максимальное количество результатов
            
        Returns:
            Список найденных решений
        """
        solutions = []
        
        try:
            # Поиск в специализированных источниках
            if application_type and application_type in self.search_sources:
                for source in self.search_sources[application_type]:
                    try:
                        source_solutions = self._search_in_source(
                            error_text, source, application_type, max_results
                        )
                        solutions.extend(source_solutions)
                    except Exception as e:
                        logger.error(f"Ошибка поиска в {source}: {e}")
            
            # Общий поиск в Google (если доступен)
            google_solutions = self._search_google(error_text, application_type, max_results)
            solutions.extend(google_solutions)
            
            # Удаление дубликатов и сортировка по релевантности
            unique_solutions = self._deduplicate_solutions(solutions)
            return unique_solutions[:max_results]
            
        except Exception as e:
            logger.error(f"Ошибка веб-поиска: {e}")
            return []
    
    def _search_google(self, query: str, application_type: str = None, 
                      max_results: int = 3) -> List[Dict]:
        """Поиск в Google (имитация)"""
        try:
            # Добавление контекста к запросу
            if application_type:
                query = f"{query} {application_type} решение"
            
            # Здесь можно использовать Google Search API или парсинг
            # Для демонстрации возвращаем заглушку
            return [{
                'title': f'Поиск: {query}',
                'url': f'https://www.google.com/search?q={quote_plus(query)}',
                'snippet': f'Найдено решений для: {query}',
                'source': 'Google Search',
                'relevance': 0.7
            }]
            
        except Exception as e:
            logger.error(f"Ошибка поиска в Google: {e}")
            return []
    
    def _search_in_source(self, query: str, source: str, application_type: str, 
                         max_results: int) -> List[Dict]:
        """Поиск в конкретном источнике"""
        try:
            # Построение URL для поиска
            search_url = self._build_search_url(source, query, application_type)
            
            # Получение страницы
            response = self.session.get(search_url, timeout=10)
            response.raise_for_status()
            
            # Парсинг результатов
            soup = BeautifulSoup(response.content, 'html.parser')
            results = self._parse_search_results(soup, source, max_results)
            
            return results
            
        except Exception as e:
            logger.error(f"Ошибка поиска в {source}: {e}")
            return []
    
    def _build_search_url(self, source: str, query: str, application_type: str) -> str:
        """Построение URL для поиска"""
        if '1c.ru' in source:
            return f"{source}/search?q={quote_plus(query)}"
        elif 'infostart.ru' in source:
            return f"{source}/search?q={quote_plus(query)}"
        elif 'microsoft.com' in source:
            return f"{source}/search?q={quote_plus(query)}"
        elif 'stackoverflow.com' in source:
            return f"{source}/search?q={quote_plus(query)}"
        else:
            return f"{source}/search?q={quote_plus(query)}"
    
    def _parse_search_results(self, soup: BeautifulSoup, source: str, 
                            max_results: int) -> List[Dict]:
        """Парсинг результатов поиска"""
        results = []
        
        try:
            # Поиск ссылок на результаты
            links = soup.find_all('a', href=True)
            
            for link in links[:max_results * 2]:  # Берем больше для фильтрации
                href = link.get('href')
                title = link.get_text(strip=True)
                
                # Фильтрация релевантных ссылок
                if self._is_relevant_link(href, title, source):
                    result = {
                        'title': title,
                        'url': self._normalize_url(href, source),
                        'snippet': self._extract_snippet(link),
                        'source': source,
                        'relevance': self._calculate_relevance(title, href)
                    }
                    results.append(result)
            
            # Сортировка по релевантности
            results.sort(key=lambda x: x['relevance'], reverse=True)
            return results[:max_results]
            
        except Exception as e:
            logger.error(f"Ошибка парсинга результатов: {e}")
            return []
    
    def _is_relevant_link(self, href: str, title: str, source: str) -> bool:
        """Проверка релевантности ссылки"""
        if not href or not title:
            return False
        
        # Исключение служебных ссылок
        exclude_patterns = [
            r'^#', r'^javascript:', r'^mailto:', r'^tel:',
            r'/login', r'/register', r'/profile', r'/admin'
        ]
        
        for pattern in exclude_patterns:
            if re.search(pattern, href):
                return False
        
        # Проверка на наличие ключевых слов в заголовке
        keywords = ['ошибка', 'error', 'решение', 'solution', 'исправить', 'fix']
        title_lower = title.lower()
        
        return any(keyword in title_lower for keyword in keywords)
    
    def _normalize_url(self, href: str, source: str) -> str:
        """Нормализация URL"""
        if href.startswith('http'):
            return href
        elif href.startswith('/'):
            return f"{source.rstrip('/')}{href}"
        else:
            return f"{source.rstrip('/')}/{href}"
    
    def _extract_snippet(self, link_element) -> str:
        """Извлечение сниппета из элемента ссылки"""
        try:
            # Поиск ближайшего текстового элемента
            parent = link_element.parent
            if parent:
                text = parent.get_text(strip=True)
                # Ограничение длины
                return text[:200] + "..." if len(text) > 200 else text
            return link_element.get_text(strip=True)
        except:
            return ""
    
    def _calculate_relevance(self, title: str, url: str) -> float:
        """Расчет релевантности результата"""
        relevance = 0.5  # Базовая релевантность
        
        # Ключевые слова для повышения релевантности
        positive_keywords = ['решение', 'solution', 'исправить', 'fix', 'ошибка', 'error']
        negative_keywords = ['вопрос', 'question', 'проблема', 'problem']
        
        title_lower = title.lower()
        
        # Увеличение релевантности за положительные ключевые слова
        for keyword in positive_keywords:
            if keyword in title_lower:
                relevance += 0.2
        
        # Уменьшение релевантности за отрицательные ключевые слова
        for keyword in negative_keywords:
            if keyword in title_lower:
                relevance -= 0.1
        
        return min(1.0, max(0.0, relevance))
    
    def _deduplicate_solutions(self, solutions: List[Dict]) -> List[Dict]:
        """Удаление дубликатов решений"""
        seen_urls = set()
        unique_solutions = []
        
        for solution in solutions:
            if solution['url'] not in seen_urls:
                seen_urls.add(solution['url'])
                unique_solutions.append(solution)
        
        return unique_solutions
    
    def get_detailed_solution(self, url: str) -> Optional[Dict]:
        """Получение детального решения по URL"""
        try:
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Извлечение основного контента
            content = self._extract_main_content(soup)
            
            # Извлечение кода (если есть)
            code_blocks = self._extract_code_blocks(soup)
            
            return {
                'url': url,
                'content': content,
                'code_blocks': code_blocks,
                'title': soup.title.get_text() if soup.title else '',
                'extracted_at': time.time()
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения детального решения: {e}")
            return None
    
    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Извлечение основного контента страницы"""
        # Удаление служебных элементов
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
            element.decompose()
        
        # Поиск основного контента
        main_selectors = [
            'main', 'article', '.content', '.post-content', 
            '.entry-content', '#content', '.main-content'
        ]
        
        for selector in main_selectors:
            content = soup.select_one(selector)
            if content:
                return content.get_text(strip=True)
        
        # Fallback - весь текст страницы
        return soup.get_text(strip=True)
    
    def _extract_code_blocks(self, soup: BeautifulSoup) -> List[str]:
        """Извлечение блоков кода"""
        code_blocks = []
        
        # Поиск блоков кода
        code_elements = soup.find_all(['code', 'pre'])
        
        for element in code_elements:
            code_text = element.get_text(strip=True)
            if len(code_text) > 10:  # Минимальная длина для кода
                code_blocks.append(code_text)
        
        return code_blocks 