from database.db import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()

print("=== 填空题 ===")
cursor.execute('SELECT id, type, stem, answer FROM questions WHERE type = ? LIMIT 5', ['fill'])
for r in cursor.fetchall():
    print(f"ID:{r[0]}")
    print(f"  题干:{r[2][:80]}...")
    print(f"  答案:{r[3]}")
    print()

print("=== 大题 ===")
cursor.execute('SELECT id, type, stem, answer FROM questions WHERE type = ? LIMIT 5', ['essay'])
for r in cursor.fetchall():
    print(f"ID:{r[0]}")
    print(f"  题干:{r[2][:80]}...")
    print(f"  答案:{r[3][:100]}...")
    print()

print("=== 选择题 ===")
cursor.execute('SELECT id, type, stem, answer FROM questions WHERE type = ? LIMIT 5', ['choice'])
for r in cursor.fetchall():
    print(f"ID:{r[0]}")
    print(f"  题干:{r[2][:80]}...")
    print(f"  答案:{r[3]}")
    print()

conn.close()
