# database.py

import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
from datetime import datetime
import logging


DB_PATH = Path(__file__).parent / "database" / "bot_db.sqlite"


def create_database():
    """Создание базы данных и необходимых таблиц"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # Создание таблицы для хранения профилей пользователей
    c.execute('''
    CREATE TABLE IF NOT EXISTS user_profile (
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
    ''')

    # Создание таблицы для хранения доступа пользователей
    c.execute('''
    CREATE TABLE IF NOT EXISTS user_access (
        user_id INTEGER PRIMARY KEY,
        access_level INTEGER DEFAULT 0,
        subscription_end TIMESTAMP,
        last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES user_profile(user_id)
    )
    ''')

    # Создание таблицы для хранения результатов тестов
    c.execute('''
    CREATE TABLE IF NOT EXISTS test_results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        test_id TEXT,
        score INTEGER,
        max_score INTEGER,
        answers TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES user_profile(user_id)
    )
    ''')

    # Создание таблицы для хранения активности пользователей
    c.execute('''
    CREATE TABLE IF NOT EXISTS user_activity (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        activity_type TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES user_profile(user_id)
    )
    ''')

    # Создание таблицы для хранения истории занятий
    c.execute('''
    CREATE TABLE IF NOT EXISTS lesson_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        lesson_type TEXT,
        lesson_id TEXT,
        completion_status TEXT,
        score INTEGER,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES user_profile(user_id)
    )
    ''')

    conn.commit()
    conn.close()


def test_database():
    """Тестирование базы данных"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()


    test_user_id = 123456789


    cur.execute("""
    INSERT OR IGNORE INTO user_access 
    (user_id, referral_count, textbooks_access, theory_access, group_member)
    VALUES (?, ?, ?, ?, ?)
    """, (test_user_id, 0, False, False, False))


    cur.execute("SELECT * FROM user_access WHERE user_id = ?", (test_user_id,))
    result = cur.fetchone()
    print(f"Тестовая запись: {result}")


    cur.execute("DELETE FROM user_access WHERE user_id = ?", (test_user_id,))

    conn.commit()
    conn.close()
    print("Тест базы данных успешно завершен!")


def save_test_result(user_id: int, test_id: str, score: int, max_score: int, answers: Dict[str, Any]) -> None:
    """Сохранение результата теста"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("""
    INSERT INTO test_results (user_id, test_id, score, max_score, answers)
    VALUES (?, ?, ?, ?, ?)
    """, (user_id, test_id, score, max_score, json.dumps(answers, ensure_ascii=False)))
    
    conn.commit()
    conn.close()


def get_user_test_results(user_id: int) -> List[Dict[str, Any]]:
    """Получение всех результатов тестов пользователя"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("""
    SELECT test_id, score, max_score, timestamp, answers
    FROM test_results
    WHERE user_id = ?
    ORDER BY timestamp DESC
    """, (user_id,))
    
    results = []
    for row in cur.fetchall():
        results.append({
            'test_id': row[0],
            'score': row[1],
            'max_score': row[2],
            'timestamp': row[3],
            'answers': json.loads(row[4])
        })
    
    conn.close()
    return results


def update_user_profile(user_id: int, profile_data: Dict[str, Any]) -> None:
    """Обновление профиля пользователя"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("SELECT 1 FROM user_profile WHERE user_id = ?", (user_id,))
        exists = cursor.fetchone()
        
        current_time = datetime.now().isoformat()
        
        if exists:
            # Обновляем существующий профиль
            update_parts = []
            params = []
            for key, value in profile_data.items():
                if key in ['first_name', 'last_name', 'education_level', 'study_goals', 'rus_goal', 'math_goal']:
                    update_parts.append(f"{key} = ?")
                    params.append(value)
                elif key == 'stats' or key == 'progress_data':
                    update_parts.append("progress_data = ?")
                    params.append(json.dumps(value))
            if update_parts:
                update_parts.append("last_seen = ?")
                params.append(current_time)
                params.append(user_id)
                sql = f"UPDATE user_profile SET {', '.join(update_parts)} WHERE user_id = ?"
                cursor.execute(sql, params)
        else:
            # Создаем новый профиль
            first_name = profile_data.get('first_name', '')
            last_name = profile_data.get('last_name', '')
            education_level = profile_data.get('education_level', '')
            study_goals = profile_data.get('study_goals', '')
            rus_goal = profile_data.get('rus_goal')
            math_goal = profile_data.get('math_goal')
            if 'stats' in profile_data or 'progress_data' in profile_data:
                progress_data = profile_data.get('stats', profile_data.get('progress_data', {}))
                progress_data = json.dumps(progress_data)
            else:
                progress_data = '{}'
            cursor.execute(
                """INSERT INTO user_profile 
                   (user_id, first_name, last_name, education_level, study_goals, progress_data, last_seen, rus_goal, math_goal) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, first_name, last_name, education_level, study_goals, progress_data, current_time, rus_goal, math_goal)
            )
        cursor.execute("SELECT 1 FROM user_access WHERE user_id = ?", (user_id,))
        exists = cursor.fetchone()
        if exists:
            cursor.execute(
                "UPDATE user_access SET last_seen = ? WHERE user_id = ?",
                (current_time, user_id)
            )
        else:
            cursor.execute(
                "INSERT INTO user_access (user_id, last_seen) VALUES (?, ?)",
                (user_id, current_time)
            )
        conn.commit()
        conn.close()
        logging.info(f"Профиль пользователя {user_id} обновлен успешно")
    except Exception as e:
        logging.error(f"Ошибка при обновлении профиля пользователя: {e}")
        raise


def get_user_profile(user_id: int) -> Optional[Dict[str, Any]]:
    """Получение профиля пользователя"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute(
            """SELECT first_name, last_name, education_level, study_goals, progress_data, last_seen, rus_goal, math_goal 
               FROM user_profile WHERE user_id = ?""",
            (user_id,)
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            try:
                progress_data = json.loads(row[4]) if row[4] else {}
            except:
                progress_data = {}
            return {
                'first_name': row[0],
                'last_name': row[1],
                'education_level': row[2],
                'study_goals': row[3],
                'progress_data': progress_data,
                'last_seen': row[5],
                'rus_goal': row[6],
                'math_goal': row[7]
            }
        return None
    except Exception as e:
        logging.error(f"Ошибка при получении профиля пользователя: {e}")
        return None


def save_lesson_history(user_id: int, lesson_data: Dict[str, Any]) -> None:
    """Сохранение истории занятий пользователя"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("""
    INSERT INTO lesson_history (user_id, lesson_data)
    VALUES (?, ?)
    """, (user_id, json.dumps(lesson_data, ensure_ascii=False)))
    
    conn.commit()
    conn.close()


def get_lesson_history(user_id: int) -> List[Dict[str, Any]]:
    """Получение истории занятий пользователя"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("""
    SELECT lesson_data, completion_date
    FROM lesson_history
    WHERE user_id = ?
    ORDER BY completion_date DESC
    """, (user_id,))
    
    history = []
    for row in cur.fetchall():
        history.append({
            'lesson_data': json.loads(row[0]),
            'completion_date': row[1]
        })
    
    conn.close()
    return history


def clear_lesson_history(user_id: int) -> None:
    """Очистка истории занятий пользователя"""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    cur.execute("DELETE FROM lesson_history WHERE user_id = ?", (user_id,))
    
    conn.commit()
    conn.close()


def update_user_activity(user_id: int) -> None:
    """Обновление времени активности пользователя"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute("SELECT id FROM user_activity WHERE user_id = ?", (user_id,))
        exists = cur.fetchone()
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if exists:
            # Обновляем timestamp
            cur.execute("""
            UPDATE user_activity 
            SET timestamp = ? 
            WHERE user_id = ?
            """, (current_time, user_id))
        else:
            # Создаем новую запись
            cur.execute("""
            INSERT INTO user_activity (user_id, activity_type, timestamp)
            VALUES (?, ?, ?)
            """, (user_id, 'default', current_time))
        conn.commit()
        conn.close()
    except Exception as e:
        logging.error(f"Ошибка при обновлении времени активности: {e}")


def get_user_activity(user_id: int) -> Dict[str, Any]:
    """Получение данных об активности пользователя"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute(
            "UPDATE user_access SET last_seen = ? WHERE user_id = ?",
            (datetime.now().isoformat(), user_id)
        )
        
        cursor.execute("SELECT 1 FROM user_activity WHERE user_id = ?", (user_id,))
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute(
                "INSERT INTO user_activity (user_id, first_seen, last_seen) VALUES (?, ?, ?)",
                (user_id, datetime.now().isoformat(), datetime.now().isoformat())
            )
        else:
            cursor.execute(
                "UPDATE user_activity SET last_seen = ? WHERE user_id = ?",
                (datetime.now().isoformat(), user_id)
            )
        
        cursor.execute(
            "SELECT first_seen, last_seen, total_time FROM user_activity WHERE user_id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        
        conn.commit()
        conn.close()
        
        if row:
            return {
                'first_seen': row[0],
                'last_seen': row[1],
                'total_time': row[2] if row[2] else 0
            }
        
        return {
            'first_seen': None,
            'last_seen': None,
            'total_time': 0
        }
    except Exception as e:
        logging.error(f"Ошибка при получении данных активности пользователя: {e}")
        return {'first_seen': None, 'last_seen': None, 'total_time': 0}


if __name__ == "__main__":
    create_database()
    test_database()