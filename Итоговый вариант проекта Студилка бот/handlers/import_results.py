#handlers/import_results.py

import importlib.util
import logging
from pathlib import Path
from data_storage import user_results
import json
from typing import Dict, Any, Optional
from datetime import datetime

from data_storage import user_data_manager

BASE_DIR = Path(__file__).resolve().parent.parent  # Путь к корню


async def update_user_results_in_memory(user_id: int, subject: str, year: str, score: int, test_type: str = "demo"):
    """
    Обновляет результаты пользователя в памяти.
    
    Args:
        user_id: ID пользователя
        subject: Предмет (rus, math)
        year: Год теста (2024, 2025)
        score: Количество баллов
        test_type: Тип теста (demo, practice)
    """
    try:
        if subject not in ['rus', 'math']:
            logging.error(f"Неверный предмет: {subject}. Допустимые значения: rus, math")
            return
            
        if year not in ['2024', '2025']:
            logging.error(f"Неверный год: {year}. Допустимые значения: 2024, 2025")
            return
            
        test_id = f"{subject}_{test_type}_{year}"
        
        test_data = {
            'test_type': test_type,
            'subject': subject,
            'year': year,
            'completion_time': datetime.now().isoformat()
        }
        
        user_data_manager.save_test_results(
            user_id=user_id,
            test_id=test_id,
            score=score,
            max_score=100,
            answers=test_data
        )
        
        logging.info(f"Результаты теста импортированы для пользователя {user_id}")
        
    except Exception as e:
        logging.error(f"Ошибка при импорте результатов теста: {e}")


def load_variant_data(subject: str, year: str) -> Optional[Dict[str, Any]]:
    """
    Загружает данные варианта из Python файла в директории test_images.
    
    Args:
        subject: Предмет (rus, math)
        year: Год варианта
    
    Returns:
        Dict с данными варианта или None в случае ошибки
    """
    try:
        variant_key = "demo 1"
        data_path = BASE_DIR / "assets" / "test_images" / subject / year / variant_key / "for_code" / "variant_data.py"
        
        if not data_path.exists():
            logging.error(f"Файл с данными варианта не найден: {data_path}")
            return None
            
        spec = importlib.util.spec_from_file_location("variant_data", data_path)
        if spec is None or spec.loader is None:
            logging.error(f"Не удалось создать спецификацию модуля для {data_path}")
            return None
            
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Возвращаем данные варианта
        return module.VARIANT_DATA
            
    except Exception as e:
        logging.error(f"Ошибка при загрузке данных варианта: {e}")
        return None
