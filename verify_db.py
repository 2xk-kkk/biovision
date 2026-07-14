import sqlite3

conn = sqlite3.connect('backend/biovision.db')
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM exams")
exam_count = cursor.fetchone()[0]
print(f"试卷数量: {exam_count}")

cursor.execute("SELECT COUNT(*) FROM questions")
question_count = cursor.fetchone()[0]
print(f"题目数量: {question_count}")

print("\n所有试卷:")
cursor.execute("SELECT id, name, question_count FROM exams ORDER BY name")
for exam in cursor.fetchall():
    print(f"  {exam[0]}. {exam[1]} - {exam[2]}题")

conn.close()
