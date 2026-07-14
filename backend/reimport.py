import sqlite3
import json
import os

db_path = 'forum.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("DROP TABLE IF EXISTS questions")
cursor.execute("DROP TABLE IF EXISTS exams")
cursor.execute("DROP TABLE IF EXISTS user_answers")
print('已删除所有表')

cursor.execute('''
    CREATE TABLE exams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        file_name TEXT,
        question_count INTEGER DEFAULT 0,
        create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(name)
    )
''')

cursor.execute('''
    CREATE TABLE questions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exam_id INTEGER NOT NULL,
        number INTEGER NOT NULL,
        stem TEXT NOT NULL,
        option_a TEXT,
        option_b TEXT,
        option_c TEXT,
        option_d TEXT,
        answer TEXT,
        images TEXT,
        create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(exam_id) REFERENCES exams(id) ON DELETE CASCADE,
        UNIQUE(exam_id, number)
    )
''')

cursor.execute('''
    CREATE TABLE user_answers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        question_id INTEGER NOT NULL,
        answer TEXT,
        is_correct INTEGER DEFAULT 0,
        create_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
        FOREIGN KEY(question_id) REFERENCES questions(id) ON DELETE CASCADE,
        UNIQUE(user_id, question_id)
    )
''')
print('已重建表结构')

questions_file = os.path.join(os.path.dirname(__file__), 'questions.json')
with open(questions_file, 'r', encoding='utf-8') as f:
    data = json.load(f)

imported_count = 0
for exam_name, exam_data in data.items():
    cursor.execute('INSERT INTO exams (name, file_name, question_count) VALUES (?, ?, ?)',
                   (exam_name, exam_data.get('file', ''), exam_data.get('question_count', 0)))
    exam_id = cursor.lastrowid
    
    for q in exam_data['questions']:
        images_json = json.dumps(q.get('images') or [])
        cursor.execute('''
            INSERT INTO questions (exam_id, number, stem, option_a, option_b, option_c, option_d, answer, images)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (exam_id, q['number'], q['stem'], q['options']['A'], q['options']['B'], 
              q['options']['C'], q['options']['D'], q['answer'], images_json))
        imported_count += 1
    
    print(f'导入: {exam_name} - {len(exam_data["questions"])} 题')

conn.commit()
print(f'\n共导入 {len(data)} 套试卷，{imported_count} 道题')
conn.close()