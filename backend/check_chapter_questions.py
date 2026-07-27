from database.db import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()

cursor.execute('SELECT id, type, stem, answer FROM questions WHERE textbook = ? AND chapter = ? AND section = ? AND type = ? LIMIT 10', 
               ['必修一：分子与细胞', '第1章 走近细胞', '第1节 细胞是生命活动的基本单位', 'fill'])

print("=== 特定小节的填空题 ===")
for r in cursor.fetchall():
    print(f"ID:{r[0]}")
    print(f"  题干:{r[2][:80]}...")
    print(f"  答案:{r[3]}")
    print()

cursor.execute('SELECT id, type, stem, answer FROM questions WHERE textbook = ? AND chapter = ? AND section = ? AND type = ? LIMIT 10', 
               ['必修一：分子与细胞', '第1章 走近细胞', '第1节 细胞是生命活动的基本单位', 'essay'])

print("=== 特定小节的大题 ===")
for r in cursor.fetchall():
    print(f"ID:{r[0]}")
    print(f"  题干:{r[2][:80]}...")
    print(f"  答案:{r[3][:80]}")
    print()

conn.close()
