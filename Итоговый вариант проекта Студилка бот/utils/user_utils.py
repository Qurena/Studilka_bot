# utils/user_utils.py

import logging
import sqlite3
from datetime import datetime
from pathlib import Path

from config.bot_config import DB_PATH

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Структура для хранения данных пользователей
user_data = {}


async def init_user_data(user_id: int) -> dict:
    """Инициализация данных пользователя"""
    if user_id not in user_data:
        user_data[user_id] = {
            "points": 0,
            "tests_completed": 0,
            "invited_users": 0,
            "rus_progress": 0,
            "math_progress": 0,
            "average_score": 0,
            "correct_answers": 0,
            "wrong_answers": 0,
            "average_time": 0,
            "best_rus": 0,
            "best_math": 0,
            "rus_goal": None,
            "math_goal": None,
            "last_session1": None,
            "last_session2": None,
            "last_session3": None,
            "total_sessions": 0,
            "total_time": 0,
            "avg_session_time": 0,
            "accumulated_time": 0
        }
        logger.info(f"Созданы новые данные для пользователя {user_id}")
    return user_data[user_id]


async def track_user_time(user_id: int) -> dict:
    """Отслеживание времени пользователя в боте"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS user_activity (
            user_id INTEGER PRIMARY KEY,
            first_seen TIMESTAMP,
            last_seen TIMESTAMP,
            total_time REAL DEFAULT 0,
            last_session_start TIMESTAMP
        )
        """)

        current_time = datetime.now()

        cur.execute("""
        SELECT first_seen, last_seen, total_time, last_session_start 
        FROM user_activity 
        WHERE user_id = ?
        """, (user_id,))
        result = cur.fetchone()

        if result is None:
            cur.execute("""
            INSERT INTO user_activity 
            (user_id, first_seen, last_seen, total_time, last_session_start)
            VALUES (?, ?, ?, 0, ?)
            """, (user_id, current_time, current_time, current_time))
            total_time = 0
        else:
            first_seen, last_seen, total_time, last_session_start = result

            if last_seen:
                last_seen = datetime.strptime(last_seen, "%Y-%m-%d %H:%M:%S.%f")
                time_diff = (current_time - last_seen).total_seconds() / 60

                if time_diff <= 30:
                    total_time += time_diff
                else:
                    last_session_start = current_time


            cur.execute("""
            UPDATE user_activity 
            SET last_seen = ?,
                total_time = ?,
                last_session_start = ?
            WHERE user_id = ?
            """, (current_time, total_time, last_session_start, user_id))

        conn.commit()
        conn.close()

        return {
            "total_time": total_time,
            "last_seen": current_time.strftime("%Y-%m-%d %H:%M:%S.%f")
        }

    except Exception as e:
        logger.error(f"Ошибка при отслеживании времени: {e}")
        logger.error(f"Путь к базе данных: {DB_PATH}")
        logger.error(f"Директория существует: {Path(DB_PATH).parent.exists()}")
        logger.error(f"Права доступа к директории: {oct(Path(DB_PATH).parent.stat().st_mode)[-3:]}")
        
        return {"total_time": 0, "last_seen": None}


def format_time(minutes: float) -> str:
    total_mins = round(minutes)

    if total_mins == 0:
        return "менее минуты"

    hours = total_mins // 60
    mins = total_mins % 60

    if hours > 0:
        if mins > 0:
            return f"{hours} ч {mins} мин"
        return f"{hours} ч"
    return f"{mins} мин"
