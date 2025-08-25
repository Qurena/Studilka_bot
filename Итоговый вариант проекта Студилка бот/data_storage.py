# data_storage.py

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from database import (
    save_test_result,
    get_user_test_results,
    update_user_profile,
    get_user_profile,
    create_database,
    save_lesson_history,
    get_lesson_history,
    clear_lesson_history
)

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UserDataManager:
    def __init__(self):
        create_database()
        
    def save_test_results(self, user_id: int, test_id: str, score: int, 
                         max_score: int, answers: Dict[str, Any]) -> None:
        """Сохранение результатов теста пользователя"""
        try:
            save_test_result(user_id, test_id, score, max_score, answers)
            logger.info(f"Результаты теста сохранены для пользователя {user_id}")
        except Exception as e:
            logger.error(f"Ошибка при сохранении результатов теста: {e}")
    
    def get_user_results(self, user_id: int) -> List[Dict[str, Any]]:
        """Получение всех результатов тестов пользователя"""
        try:
            results = get_user_test_results(user_id)
            logger.info(f"Получены результаты тестов для пользователя {user_id}")
            return results
        except Exception as e:
            logger.error(f"Ошибка при получении результатов тестов: {e}")
            return []

    def update_profile(self, user_id: int, profile_data: Dict[str, Any]) -> None:
        """Обновление профиля пользователя"""
        try:
            update_user_profile(user_id, profile_data)
            logger.info(f"Профиль пользователя {user_id} обновлен")
        except Exception as e:
            logger.error(f"Ошибка при обновлении профиля пользователя: {e}")

    def get_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получение профиля пользователя"""
        try:
            profile = get_user_profile(user_id)
            if profile:
                logger.info(f"Получен профиль пользователя {user_id}")
            else:
                logger.info(f"Профиль пользователя {user_id} не найден")
            return profile
        except Exception as e:
            logger.error(f"Ошибка при получении профиля пользователя: {e}")
            return None

    def save_lesson_history(self, user_id: int, lesson_data: Dict[str, Any]) -> None:
        """Сохранение истории занятий пользователя"""
        try:
            save_lesson_history(user_id, lesson_data)
            logger.info(f"История занятий для пользователя {user_id} обновлена")
        except Exception as e:
            logger.error(f"Ошибка при сохранении истории занятий: {e}")

    def get_lesson_history(self, user_id: int) -> List[Dict[str, Any]]:
        """Получение истории занятий пользователя"""
        try:
            history = get_lesson_history(user_id)
            logger.info(f"Получена история занятий для пользователя {user_id}")
            return history
        except Exception as e:
            logger.error(f"Ошибка при получении истории занятий: {e}")
            return []

    def clear_lesson_history(self, user_id: int) -> None:
        """Очистка истории занятий пользователя"""
        try:
            clear_lesson_history(user_id)
            logger.info(f"История занятий для пользователя {user_id} очищена")
        except Exception as e:
            logger.error(f"Ошибка при очистке истории занятий: {e}")

user_data_manager = UserDataManager()
user_results = {}

