import sqlite3
import json

conn = sqlite3.connect('backend/forum.db')
cursor = conn.cursor()

cursor.execute("SELECT id, name FROM exams WHERE name LIKE '%云南%'")
result = cursor.fetchone()
if result:
    exam_id, exam_name = result
    print(f"=== {exam_name} ===")
    cursor.execute("SELECT number, images FROM questions WHERE exam_id = ? ORDER BY number", (exam_id,))
    results = cursor.fetchall()
    for number, images in results:
        if images and images != '[]':
            parsed = json.loads(images)
            print(f"  题目 {number}: {parsed}")
        else:
            print(f"  题目 {number}: 无图片")

conn.close()