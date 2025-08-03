"""
Скрипт инициализации базы данных с примерами решений
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.knowledge_base import KnowledgeBase, Solution
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_sample_data():
    """Инициализация базы данных с примерами решений"""
    
    knowledge_base = KnowledgeBase()
    
    # Примеры решений для 1С
    c1_solutions = [
        {
            "error_text": "Ошибка при выполнении запроса к базе данных",
            "solution_text": "Проверьте права доступа пользователя к базе данных и убедитесь, что соединение активно",
            "application_type": "1c",
            "error_category": "sql",
            "source": "1C Forum",
            "success_rate": 85.0,
            "tags": ["1с", "sql", "база данных", "права"],
            "steps": [
                "Проверьте настройки подключения к базе данных",
                "Убедитесь, что пользователь имеет необходимые права",
                "Проверьте активность соединения с сервером",
                "Перезапустите службу 1С:Предприятие"
            ]
        },
        {
            "error_text": "Не удалось найти процедуру",
            "solution_text": "Проверьте конфигурацию и убедитесь, что процедура существует и доступна",
            "application_type": "1c",
            "error_category": "config",
            "source": "Infostart",
            "success_rate": 90.0,
            "tags": ["1с", "конфигурация", "процедура"],
            "steps": [
                "Проверьте наличие процедуры в конфигурации",
                "Убедитесь, что процедура экспортирована",
                "Проверьте права доступа к процедуре",
                "Обновите конфигурацию базы данных"
            ]
        },
        {
            "error_text": "Недостаточно прав для выполнения операции",
            "solution_text": "Настройте роли пользователя в конфигурации 1С",
            "application_type": "1c",
            "error_category": "rights",
            "source": "1C Documentation",
            "success_rate": 95.0,
            "tags": ["1с", "права", "роли", "доступ"],
            "steps": [
                "Откройте конфигуратор",
                "Перейдите в раздел 'Роли'",
                "Найдите нужную роль и настройте права",
                "Обновите конфигурацию базы данных"
            ]
        }
    ]
    
    # Примеры решений для Windows
    windows_solutions = [
        {
            "error_text": "Системная ошибка: не удалось запустить службу",
            "solution_text": "Проверьте зависимости службы и перезапустите её",
            "application_type": "windows",
            "error_category": "service",
            "source": "Microsoft Support",
            "success_rate": 80.0,
            "tags": ["windows", "служба", "система"],
            "steps": [
                "Откройте 'Службы' (services.msc)",
                "Найдите проблемную службу",
                "Проверьте зависимости службы",
                "Перезапустите службу"
            ]
        },
        {
            "error_text": "Синий экран смерти (BSOD)",
            "solution_text": "Обновите драйверы и проверьте совместимость оборудования",
            "application_type": "windows",
            "error_category": "bsod",
            "source": "Microsoft Answers",
            "success_rate": 75.0,
            "tags": ["windows", "bsod", "драйверы", "синий экран"],
            "steps": [
                "Запишите код ошибки BSOD",
                "Обновите драйверы устройств",
                "Проверьте совместимость оборудования",
                "Запустите диагностику памяти"
            ]
        }
    ]
    
    # Примеры решений для Office
    office_solutions = [
        {
            "error_text": "Ошибка в формуле Excel",
            "solution_text": "Проверьте синтаксис формулы и ссылки на ячейки",
            "application_type": "office",
            "error_category": "excel",
            "source": "Microsoft Office Support",
            "success_rate": 90.0,
            "tags": ["excel", "формула", "ошибка"],
            "steps": [
                "Проверьте синтаксис формулы",
                "Убедитесь, что все ссылки корректны",
                "Проверьте типы данных в ячейках",
                "Используйте функцию 'Проверить ошибки'"
            ]
        },
        {
            "error_text": "Word не может открыть документ",
            "solution_text": "Попробуйте открыть документ в безопасном режиме или восстановить его",
            "application_type": "office",
            "error_category": "word",
            "source": "Microsoft Office Support",
            "success_rate": 85.0,
            "tags": ["word", "документ", "открытие"],
            "steps": [
                "Попробуйте открыть в безопасном режиме",
                "Используйте функцию восстановления документа",
                "Проверьте права доступа к файлу",
                "Попробуйте открыть копию документа"
            ]
        }
    ]
    
    # Примеры решений для браузеров
    browser_solutions = [
        {
            "error_text": "Ошибка соединения с сервером",
            "solution_text": "Проверьте интернет-соединение и настройки прокси",
            "application_type": "browser",
            "error_category": "connection",
            "source": "Browser Support",
            "success_rate": 85.0,
            "tags": ["браузер", "соединение", "интернет"],
            "steps": [
                "Проверьте интернет-соединение",
                "Очистите кэш браузера",
                "Проверьте настройки прокси",
                "Попробуйте другой браузер"
            ]
        },
        {
            "error_text": "JavaScript ошибка на странице",
            "solution_text": "Обновите браузер и проверьте настройки JavaScript",
            "application_type": "browser",
            "error_category": "javascript",
            "source": "Browser Support",
            "success_rate": 80.0,
            "tags": ["браузер", "javascript", "скрипт"],
            "steps": [
                "Обновите браузер до последней версии",
                "Включите JavaScript в настройках",
                "Очистите кэш и куки",
                "Попробуйте режим инкогнито"
            ]
        }
    ]
    
    # Объединение всех решений
    all_solutions = c1_solutions + windows_solutions + office_solutions + browser_solutions
    
    # Добавление решений в базу
    added_count = 0
    for solution_data in all_solutions:
        solution = Solution(
            id=None,
            error_text=solution_data["error_text"],
            solution_text=solution_data["solution_text"],
            application_type=solution_data["application_type"],
            error_category=solution_data["error_category"],
            source=solution_data["source"],
            success_rate=solution_data["success_rate"],
            created_at=datetime.now().isoformat(),
            tags=solution_data["tags"],
            steps=solution_data["steps"]
        )
        
        if knowledge_base.add_solution(solution):
            added_count += 1
            logger.info(f"Добавлено решение: {solution_data['error_text'][:50]}...")
        else:
            logger.error(f"Ошибка добавления решения: {solution_data['error_text'][:50]}...")
    
    logger.info(f"Инициализация завершена. Добавлено {added_count} решений из {len(all_solutions)}")
    
    # Показать статистику
    stats = knowledge_base.get_statistics()
    logger.info(f"Статистика базы знаний:")
    logger.info(f"- Всего решений: {stats.get('total_solutions', 0)}")
    logger.info(f"- Средний рейтинг: {stats.get('avg_success_rate', 0):.1f}%")
    logger.info(f"- Типы приложений: {stats.get('application_stats', {})}")

if __name__ == "__main__":
    print("Инициализация базы знаний с примерами решений...")
    init_sample_data()
    print("Инициализация завершена!") 