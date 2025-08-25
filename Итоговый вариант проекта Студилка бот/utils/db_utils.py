# utils/db_utils.py

import logging
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Optional, Dict

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Путь к базе данных
DB_PATH = Path(__file__).parent.parent / "database" / "bot_db.sqlite"


def init_db():
    """Инициализация базы данных"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Удаляем старую таблицу, если она существует
    cur.execute("DROP TABLE IF EXISTS user_activity")

    # Создаем таблицу с правильными названиями колонок
    cur.execute("""
    CREATE TABLE IF NOT EXISTS user_activity (
        user_id INTEGER PRIMARY KEY,
        first_seen TIMESTAMP,
        last_seen TIMESTAMP,
        total_time REAL DEFAULT 0,
        last_session_start TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()
    logger.info("База данных определена")


async def get_user_time(user_id: int) -> Optional[Dict[str, Any]]:
    """Получение данных о времени пользователя"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    SELECT first_seen, last_seen, total_time, last_session_start
    FROM user_time
    WHERE user_id = ?
    """, (user_id,))

    result = cur.fetchone()
    conn.close()

    if result:
        return {
            "first_seen": datetime.fromisoformat(result[0]) if result[0] else None,
            "last_seen": datetime.fromisoformat(result[1]) if result[1] else None,
            "total_time": float(result[2]) if result[2] is not None else 0.0,
            "last_session_start": datetime.fromisoformat(result[3]) if result[3] else None
        }
    return None


async def update_user_time(user_id: int, total_time: float = None):
    """Обновление времени пользователя"""
    global current_total_time
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()

        current_time = datetime.now()

        # Проверяем
        cur.execute("""
        SELECT last_seen, total_time 
        FROM user_time 
        WHERE user_id = ?
        """, (user_id,))
        result = cur.fetchone()

        if not result:
            # Создаем
            cur.execute("""
            INSERT INTO user_time (user_id, first_seen, last_seen, total_time, last_session_start)
            VALUES (?, ?, ?, ?, ?)
            """, (user_id, current_time, current_time, total_time or 0.0, current_time))
        else:
            last_seen = datetime.fromisoformat(result[0]) if result[0] else None
            current_total_time = float(result[1]) if result[1] is not None else 0.0

            if last_seen:
                time_diff = (current_time - last_seen).total_seconds() / 60
                if time_diff <= 30:  # Если перерыв меньше 30 минут
                    current_total_time += time_diff

            # Обновляем
            cur.execute("""
            UPDATE user_time 
            SET last_seen = ?,
                total_time = ?
            WHERE user_id = ?
            """, (current_time, current_total_time, user_id))

        conn.commit()
        conn.close()
        logger.info(f"Время пользователя {user_id} обновлено. Общее время: {current_total_time:.1f} мин")

    except Exception as e:
        logger.error(f"Ошибка при обновлении времени: {e}")


async def start_new_session(user_id: int):
    """Начало новой сессии пользователя"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    current_time = datetime.now()

    cur.execute("""
    UPDATE user_time 
    SET last_session_start = ?,
        last_seen = ?
    WHERE user_id = ?
    """, (current_time, current_time, user_id))

    conn.commit()
    conn.close()
