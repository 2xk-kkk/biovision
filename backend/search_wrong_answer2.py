from database.db import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()

cursor.execute('SELECT id, type, stem, answer, section FROM questions WHERE answer LIKE ?', ['%统一了动植物%'])

results = cursor.fetchall()
print(f"找到 {len(results)} 条结果")
for r in results:
    print(f"ID:{r[0]}")
    print(f"  题型:{r[1]}")
    print(f"  小节:{r[4]}")
    print(f"  题干:{r[2][:100]}...")
    print(f"  答案:{r[3]}")
    print()

conn.close()
