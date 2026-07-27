from database.db import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()

cursor.execute('SELECT id, stem, answer, analysis FROM questions WHERE type = ? AND section = ? LIMIT 10', ['choice', '专项训练'])

print("选择题解析情况：")
for r in cursor.fetchall():
    print(f"ID:{r[0]}")
    print(f"  题干:{r[1][:60]}...")
    print(f"  答案:{r[2]}")
    print(f"  解析:{r[3][:80]}..." if r[3] else "  解析:空")
    print()

conn.close()
