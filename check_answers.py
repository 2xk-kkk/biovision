import sqlite3

DB_PATH = r"d:\15821\biovision\backend\forum.db"

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute('SELECT id, name FROM exams WHERE name LIKE "%云南%"')
exams = cursor.fetchall()

for exam_id, exam_name in exams:
    print(f"\n=== {exam_name} (ID={exam_id}) ===")
    
    cursor.execute('SELECT COUNT(*) FROM questions WHERE exam_id = ?', (exam_id,))
    total = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM questions WHERE exam_id = ? AND answer IS NOT NULL AND answer != ""', (exam_id,))
    with_answers = cursor.fetchone()[0]
    
    print(f"题目总数: {total}")
    print(f"有答案的题目数: {with_answers}")
    print(f"has_answers: {with_answers > 0}")
    
    cursor.execute('SELECT number, answer FROM questions WHERE exam_id = ? AND answer IS NOT NULL AND answer != "" LIMIT 5', (exam_id,))
    answers = cursor.fetchall()
    print("前5个答案:")
    for num, ans in answers:
        print(f"  题号{num}: {ans}")

conn.close()