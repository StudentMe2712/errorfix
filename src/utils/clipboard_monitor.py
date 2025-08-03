"""
Модуль для мониторинга буфера обмена и автоматического распознавания скриншотов
"""

import time
import logging
import threading
from typing import Optional, Callable, Dict
from pathlib import Path
import tempfile
import hashlib

try:
    import win32clipboard
    import win32con
    import win32gui
    import win32api
    WINDOWS_AVAILABLE = True
except ImportError:
    WINDOWS_AVAILABLE = False
    logging.warning("win32clipboard не установлен. Мониторинг буфера недоступен.")

try:
    from PIL import ImageGrab, Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    logging.warning("PIL не установлен. Захват изображений недоступен.")

logger = logging.getLogger(__name__)

class ClipboardMonitor:
    """Монитор буфера обмена для автоматического распознавания скриншотов"""
    
    def __init__(self, callback: Optional[Callable] = None):
        self.callback = callback
        self.is_monitoring = False
        self.monitor_thread = None
        self.last_clipboard_hash = None
        self.supported_formats = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}
        
        # Проверка доступности
        self.windows_available = WINDOWS_AVAILABLE
        self.pil_available = PIL_AVAILABLE
        
        if not self.windows_available:
            logger.warning("Мониторинг буфера обмена недоступен (только Windows)")
    
    def start_monitoring(self) -> bool:
        """
        Запуск мониторинга буфера обмена
        
        Returns:
            True если успешно запущен
        """
        if not self.windows_available:
            logger.error("Мониторинг буфера недоступен на данной платформе")
            return False
        
        if self.is_monitoring:
            logger.warning("Мониторинг уже запущен")
            return False
        
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("Мониторинг буфера обмена запущен")
        return True
    
    def stop_monitoring(self):
        """Остановка мониторинга буфера обмена"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
        
        logger.info("Мониторинг буфера обмена остановлен")
    
    def _monitor_loop(self):
        """Основной цикл мониторинга"""
        while self.is_monitoring:
            try:
                # Проверка буфера обмена
                self._check_clipboard()
                time.sleep(1)  # Проверка каждую секунду
                
            except Exception as e:
                logger.error(f"Ошибка в цикле мониторинга: {e}")
                time.sleep(5)  # Пауза при ошибке
    
    def _check_clipboard(self):
        """Проверка содержимого буфера обмена"""
        try:
            win32clipboard.OpenClipboard()
            
            # Проверка наличия изображения в буфере
            if win32clipboard.IsClipboardFormatAvailable(win32con.CF_DIB):
                image_data = win32clipboard.GetClipboardData(win32con.CF_DIB)
                
                # Создание хеша для проверки изменений
                current_hash = hashlib.md5(image_data).hexdigest()
                
                if current_hash != self.last_clipboard_hash:
                    self.last_clipboard_hash = current_hash
                    self._process_clipboard_image(image_data)
            
            win32clipboard.CloseClipboard()
            
        except Exception as e:
            logger.error(f"Ошибка проверки буфера обмена: {e}")
    
    def _process_clipboard_image(self, image_data: bytes):
        """
        Обработка изображения из буфера обмена
        
        Args:
            image_data: Данные изображения
        """
        try:
            # Сохранение изображения во временный файл
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                temp_file.write(image_data)
                temp_path = temp_file.name
            
            # Проверка что это действительно изображение
            try:
                with Image.open(temp_path) as img:
                    # Проверка размера (исключаем слишком маленькие изображения)
                    if img.width < 100 or img.height < 100:
                        logger.debug("Изображение слишком маленькое, пропускаем")
                        return
                    
                    # Уведомление о новом изображении
                    if self.callback:
                        self.callback(temp_path)
                    else:
                        logger.info(f"Обнаружено новое изображение в буфере: {temp_path}")
                        
            except Exception as e:
                logger.debug(f"Файл не является изображением: {e}")
                # Удаление временного файла
                Path(temp_path).unlink(missing_ok=True)
                
        except Exception as e:
            logger.error(f"Ошибка обработки изображения из буфера: {e}")
    
    def capture_screenshot(self) -> Optional[str]:
        """
        Захват скриншота экрана
        
        Returns:
            Путь к сохраненному изображению или None
        """
        if not self.pil_available:
            logger.error("Захват скриншота недоступен (PIL не установлен)")
            return None
        
        try:
            # Захват экрана
            screenshot = ImageGrab.grab()
            
            # Сохранение во временный файл
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                screenshot.save(temp_file.name, 'PNG')
                return temp_file.name
                
        except Exception as e:
            logger.error(f"Ошибка захвата скриншота: {e}")
            return None
    
    def capture_window_screenshot(self, window_title: str = None) -> Optional[str]:
        """
        Захват скриншота конкретного окна
        
        Args:
            window_title: Заголовок окна (если None, захватывается активное окно)
            
        Returns:
            Путь к сохраненному изображению или None
        """
        if not self.windows_available or not self.pil_available:
            logger.error("Захват окна недоступен")
            return None
        
        try:
            if window_title:
                # Поиск окна по заголовку
                hwnd = win32gui.FindWindow(None, window_title)
                if not hwnd:
                    logger.warning(f"Окно с заголовком '{window_title}' не найдено")
                    return None
            else:
                # Активное окно
                hwnd = win32gui.GetForegroundWindow()
            
            # Получение координат окна
            rect = win32gui.GetWindowRect(hwnd)
            x, y, x1, y1 = rect
            
            # Захват области окна
            screenshot = ImageGrab.grab(bbox=(x, y, x1, y1))
            
            # Сохранение во временный файл
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                screenshot.save(temp_file.name, 'PNG')
                return temp_file.name
                
        except Exception as e:
            logger.error(f"Ошибка захвата окна: {e}")
            return None
    
    def get_active_window_info(self) -> Optional[Dict]:
        """
        Получение информации об активном окне
        
        Returns:
            Информация об окне или None
        """
        if not self.windows_available:
            return None
        
        try:
            hwnd = win32gui.GetForegroundWindow()
            window_title = win32gui.GetWindowText(hwnd)
            class_name = win32gui.GetClassName(hwnd)
            
            return {
                'title': window_title,
                'class': class_name,
                'handle': hwnd
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения информации об окне: {e}")
            return None
    
    def is_image_file(self, file_path: str) -> bool:
        """
        Проверка является ли файл изображением
        
        Args:
            file_path: Путь к файлу
            
        Returns:
            True если это изображение
        """
        try:
            with Image.open(file_path) as img:
                return True
        except Exception:
            return False
    
    def cleanup_temp_files(self):
        """Очистка временных файлов"""
        try:
            temp_dir = Path(tempfile.gettempdir())
            for temp_file in temp_dir.glob("clipboard_*.png"):
                try:
                    temp_file.unlink()
                except Exception as e:
                    logger.debug(f"Не удалось удалить временный файл {temp_file}: {e}")
        except Exception as e:
            logger.error(f"Ошибка очистки временных файлов: {e}")

class ClipboardHandler:
    """Обработчик событий буфера обмена"""
    
    def __init__(self, error_processor):
        self.error_processor = error_processor
        self.monitor = ClipboardMonitor(callback=self._on_new_image)
    
    def _on_new_image(self, image_path: str):
        """
        Обработчик нового изображения в буфере
        
        Args:
            image_path: Путь к изображению
        """
        try:
            logger.info(f"Обработка нового изображения: {image_path}")
            
            # Обработка изображения через основной процессор
            result = self.error_processor.process_error_screenshot(image_path)
            
            if result:
                logger.info("Изображение успешно обработано")
                # Здесь можно добавить уведомления пользователю
            else:
                logger.warning("Не удалось обработать изображение")
                
        except Exception as e:
            logger.error(f"Ошибка обработки изображения из буфера: {e}")
    
    def start_monitoring(self):
        """Запуск мониторинга"""
        return self.monitor.start_monitoring()
    
    def stop_monitoring(self):
        """Остановка мониторинга"""
        self.monitor.stop_monitoring()
    
    def capture_screenshot(self):
        """Захват скриншота"""
        return self.monitor.capture_screenshot()
    
    def capture_window_screenshot(self, window_title: str = None):
        """Захват скриншота окна"""
        return self.monitor.capture_window_screenshot(window_title) 