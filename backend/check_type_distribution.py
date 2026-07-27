from database.db import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()

cursor.execute('SELECT type, COUNT(*) FROM questions WHERE section = ? GROUP BY type', ['专项训练'])
results = cursor.fetchall()
print("专项训练题型分布：")
for r in results:
    print(f"  {r[0]}: {r[1]} 道")

print()

cursor.execute('SELECT type, stem, answer FROM questions WHERE section = ? AND type = ? LIMIT 3', ['专项训练', 'essay'])
print("大题示例：")
for r in cursor.fetchall():
    print(f"  题干:{r[1][:60]}...")
    print(f"  答案:{r[2][:80]}...")
    print()

conn.close()
