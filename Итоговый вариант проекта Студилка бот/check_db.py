# check_db.py

import sqlite3
from pathlib import Path
import os

DB_PATH = Path(__file__).parent / "database" / "bot_db.sqlite"

def check_database():
    print(f"Проверка базы данных по пути: {DB_PATH}")
    print(f"База данных существует: {os.path.exists(DB_PATH)}")
    
    if not os.path.exists(DB_PATH):
        print("База данных не найдена!")
        return
        
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    try:
        # Получаем список всех таблиц
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cur.fetchall()
        
        print("\nСуществующие таблицы:")
        for table in tables:
            table_name = table[0]
            print(f"\nТаблица: {table_name}")
            
            # Получаем структуру таблицы
            cur.execute(f"PRAGMA table_info({table_name});")
            columns = cur.fetchall()
            print("Колонки:")
            for col in columns:
                print(f"  - {col[1]} ({col[2]})")
                
            # Получаем количество записей
            cur.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cur.fetchone()[0]
            print(f"Количество записей: {count}")
            
    except Exception as e:
        print(f"Ошибка при проверке базы данных: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_database() 