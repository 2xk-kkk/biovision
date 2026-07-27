from database.db import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()

cursor.execute('SELECT id, stem, answer, analysis FROM questions WHERE stem LIKE ?', ['%关于病毒的叙述%'])

results = cursor.fetchall()
print(f"找到 {len(results)} 条结果")
for r in results:
    print(f"ID:{r[0]}")
    print(f"  题干:{r[1]}")
    print(f"  答案:{r[2]}")
    print(f"  解析:{r[3]}")
    print()

conn.close()
