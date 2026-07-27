from database.db import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()

cursor.execute('SELECT id, type, stem, answer, section FROM questions WHERE type = ? AND section = ? LIMIT 10', ['essay', '专项训练'])

results = cursor.fetchall()
print(f"找到 {len(results)} 条专项训练大题")
for r in results:
    print(f"ID:{r[0]}")
    print(f"  题干:{r[2][:80]}...")
    print(f"  答案:{r[3]}")
    print()

conn.close()
