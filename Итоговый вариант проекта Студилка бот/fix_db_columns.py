# fix_db_columns.py

import sqlite3
import logging
import sys
from pathlib import Path
from datetime import datetime

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Путь к базе данных
DB_PATH = Path(__file__).resolve().parent / "database" / "bot_db.sqlite"

def fix_user_activity_columns():
    """Исправляет имена столбцов в таблице user_activity"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("PRAGMA table_info(user_activity)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        logger.info(f"Текущие столбцы таблицы user_activity: {column_names}")
        
        if 'first_activity' in column_names or 'last_activity' in column_names:
            logger.info("Нужно переименовать столбцы. Создаю временную таблицу...")
            
            cursor.execute("""
            CREATE TABLE user_activity_new (
                user_id INTEGER PRIMARY KEY,
                first_seen TIMESTAMP,
                last_seen TIMESTAMP,
                total_time REAL DEFAULT 0,
                last_session_start TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES user_access(user_id)
            )
            """)
            
            cursor.execute("""
            INSERT INTO user_activity_new (user_id, first_seen, last_seen, total_time, last_session_start)
            SELECT user_id, 
                   COALESCE(first_activity, first_seen, CURRENT_TIMESTAMP) as first_seen, 
                   COALESCE(last_activity, last_seen, CURRENT_TIMESTAMP) as last_seen, 
                   total_time,
                   COALESCE(last_session_start, CURRENT_TIMESTAMP) as last_session_start
            FROM user_activity
            """)
            
            cursor.execute("DROP TABLE user_activity")
            
            cursor.execute("ALTER TABLE user_activity_new RENAME TO user_activity")
            
            logger.info("Таблица user_activity успешно обновлена с новыми именами столбцов")
        else:
            logger.info("Столбцы уже имеют правильные имена")
            
            # Проверяем, есть ли столбец last_session_start
            if 'last_session_start' not in column_names:
                logger.info("Добавляю столбец last_session_start...")
                cursor.execute("ALTER TABLE user_activity ADD COLUMN last_session_start TIMESTAMP")
                cursor.execute("UPDATE user_activity SET last_session_start = CURRENT_TIMESTAMP")
                logger.info("Столбец last_session_start добавлен")
        
        conn.commit()
        conn.close()
        logger.info("Операция завершена успешно!")
        return True
    except Exception as e:
        logger.error(f"Ошибка при исправлении имен столбцов: {e}")
        return False

def fix_database_columns():
    """Добавляет недостающие колонки в таблицы базы данных"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(user_profile)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'rus_goal' not in columns:
            logger.info("Добавляем колонку rus_goal в user_profile")
            cursor.execute("ALTER TABLE user_profile ADD COLUMN rus_goal INTEGER")
        
        if 'math_goal' not in columns:
            logger.info("Добавляем колонку math_goal в user_profile")
            cursor.execute("ALTER TABLE user_profile ADD COLUMN math_goal INTEGER")
        
        if 'last_seen' not in columns:
            logger.info("Добавляем колонку last_seen в user_profile")
            cursor.execute("ALTER TABLE user_profile ADD COLUMN last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP")

        cursor.execute("PRAGMA table_info(user_access)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'last_seen' not in columns:
            logger.info("Добавляем колонку last_seen в user_access")
            cursor.execute("ALTER TABLE user_access ADD COLUMN last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP")

        conn.commit()
        conn.close()
        logger.info("Структура базы данных успешно обновлена")
        
    except Exception as e:
        logger.error(f"Ошибка при обновлении структуры базы данных: {e}")
        raise

def add_missing_columns():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(user_profile);")
    columns = [row[1] for row in cur.fetchall()]
    required = [
        ("education_level", "TEXT"),
        ("study_goals", "TEXT"),
        ("progress_data", "TEXT")
    ]
    for col, col_type in required:
        if col not in columns:
            print(f"Добавляю столбец {col} в user_profile...")
            try:
                cur.execute(f"ALTER TABLE user_profile ADD COLUMN {col} {col_type};")
                print(f"Столбец {col} успешно добавлен.")
            except Exception as e:
                print(f"Ошибка при добавлении столбца {col}: {e}")
        else:
            print(f"Столбец {col} уже существует.")
    conn.commit()
    cur.execute("PRAGMA table_info(user_profile);")
    columns_after = [row[1] for row in cur.fetchall()]
    print("Текущие столбцы user_profile:", columns_after)
    conn.close()
    print("Проверка и добавление столбцов завершены.")

def recreate_user_profile_table():
    print("[DEBUG] Вызвана recreate_user_profile_table()")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(user_profile);")
    columns = [row[1] for row in cur.fetchall()]
    print(f"[DEBUG] Текущие столбцы user_profile: {columns}")
    required = ["education_level", "study_goals", "progress_data"]
    if all(col in columns for col in required):
        print("Все нужные столбцы уже есть в user_profile.")
        conn.close()
        return
    print("Пересоздаю таблицу user_profile с нужными столбцами...")
    cur.execute("""
        CREATE TABLE user_profile_new (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            rus_goal INTEGER DEFAULT 0,
            math_goal INTEGER DEFAULT 0,
            education_level TEXT,
            study_goals TEXT,
            progress_data TEXT
        )
    """)
    print("[DEBUG] Создана user_profile_new")
    cur.execute("""
        INSERT INTO user_profile_new (user_id, username, first_name, last_name, registration_date, last_seen, rus_goal, math_goal)
        SELECT user_id, username, first_name, last_name, registration_date, last_seen, rus_goal, math_goal FROM user_profile
    """)
    print("[DEBUG] Данные скопированы в user_profile_new")
    cur.execute("DROP TABLE user_profile")
    print("[DEBUG] Старая user_profile удалена")
    cur.execute("ALTER TABLE user_profile_new RENAME TO user_profile")
    print("[DEBUG] user_profile_new переименована в user_profile")
    conn.commit()
    cur.execute("PRAGMA table_info(user_profile);")
    columns_after = [row[1] for row in cur.fetchall()]
    print("[DEBUG] Итоговые столбцы user_profile:", columns_after)
    conn.close()
    print("Таблица user_profile успешно пересоздана со всеми нужными столбцами.")

def force_recreate_user_profile_table():
    print("[FORCE] Полное пересоздание таблицы user_profile...")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("DROP TABLE IF EXISTS user_profile")
    print("[FORCE] user_profile удалена (если была)")

    cur.execute("""
        CREATE TABLE user_profile (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            rus_goal INTEGER DEFAULT 0,
            math_goal INTEGER DEFAULT 0,
            education_level TEXT,
            study_goals TEXT,
            progress_data TEXT
        )
    """)
    print("[FORCE] user_profile создана с нужными столбцами")
    conn.commit()
    conn.close()
    print("[FORCE] Полное пересоздание user_profile завершено.")

if __name__ == "__main__":
    print(f"[DEBUG] Исправление имен столбцов в базе данных: {DB_PATH}")
    force_recreate_user_profile_table()
    success = fix_user_activity_columns()
    fix_database_columns()
    print("[DEBUG] Вызов recreate_user_profile_table()...")
    recreate_user_profile_table()
    add_missing_columns()
    sys.exit(0 if success else 1)