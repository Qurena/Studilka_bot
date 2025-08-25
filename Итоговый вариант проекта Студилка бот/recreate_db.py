#recreate_db.py

from database import create_database
import os
import sqlite3

# Путь к базе данных
DB_PATH = "database/bot_db.sqlite"

# Удаляем существующую базу данных, если она есть
if os.path.exists(DB_PATH):
    try:
        os.remove(DB_PATH)
        print(f"Существующая база данных удалена: {DB_PATH}")
    except Exception as e:
        print(f"Ошибка при удалении базы данных: {e}")

# Создаем новую базу данных
try:
    create_database()
    
    # Проверяем структуру созданной базы данных
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    
    # Получаем список всех таблиц
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cur.fetchall()
    
    print("\nСозданные таблицы:")
    for table in tables:
        table_name = table[0]
        print(f"\nСтруктура таблицы {table_name}:")
        cur.execute(f"PRAGMA table_info({table_name});")
        columns = cur.fetchall()
        for column in columns:
            print(f"  - {column[1]} ({column[2]})")
    
    conn.close()
    print("\nБаза данных успешно пересоздана!")
    
except Exception as e:
    print(f"Ошибка при создании базы данных: {e}") 