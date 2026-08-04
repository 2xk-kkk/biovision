import sqlite3

# 检查 database/forum.db
db_path = 'database/forum.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("database/forum.db 中的表:", tables)

table_names = [t[0] for t in tables]
if 'questions' in table_names:
    print("\nquestions 表存在!")
    cursor.execute("SELECT COUNT(*) FROM questions")
    count = cursor.fetchone()[0]
    print(f"questions 表有 {count} 条记录")
    
    # 查询不同的 textbook
    cursor.execute("SELECT DISTINCT textbook FROM questions WHERE textbook IS NOT NULL AND textbook != ''")
    textbooks = cursor.fetchall()
    print("\n所有教材:")
    for tb in textbooks:
        print(f"  {tb[0]}")
    
    # 查询选修一的章节
    cursor.execute("SELECT DISTINCT textbook, chapter FROM questions WHERE textbook LIKE '%稳态%'")
    rows = cursor.fetchall()
    print("\n选修一的章节:")
    for r in rows:
        print(f"  textbook={r[0]}, chapter={r[1]}")
else:
    print("\nquestions 表不存在!")

conn.close()
