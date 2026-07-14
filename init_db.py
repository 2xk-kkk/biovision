import sqlite3
import os

db_path = 'backend/biovision.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cursor.fetchall()]
print("当前表:", tables)

if 'exams' not in tables:
    print("创建exams表...")
    cursor.execute('''
        CREATE TABLE exams (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT DEFAULT '',
            question_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

if 'questions' not in tables:
    print("创建questions表...")
    cursor.execute('''
        CREATE TABLE questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            exam_id INTEGER NOT NULL,
            number INTEGER NOT NULL,
            stem TEXT NOT NULL,
            option_a TEXT DEFAULT '',
            option_b TEXT DEFAULT '',
            option_c TEXT DEFAULT '',
            option_d TEXT DEFAULT '',
            answer TEXT DEFAULT '',
            images TEXT DEFAULT '',
            FOREIGN KEY (exam_id) REFERENCES exams(id)
        )
    ''')

if 'user_answers' not in tables:
    print("创建user_answers表...")
    cursor.execute('''
        CREATE TABLE user_answers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            exam_id INTEGER NOT NULL,
            question_id INTEGER NOT NULL,
            answer TEXT DEFAULT '',
            is_correct INTEGER DEFAULT 0,
            answered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

conn.commit()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [t[0] for t in cursor.fetchall()]
print("创建后表:", tables)

conn.close()
print("数据库初始化完成")
