from database.db import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()

cursor.execute("PRAGMA table_info(questions)")
columns = [col[1] for col in cursor.fetchall()]
print("当前列：", columns)

if 'analysis' not in columns:
    cursor.execute("ALTER TABLE questions ADD COLUMN analysis TEXT")
    conn.commit()
    print("已添加 analysis 列")
else:
    print("analysis 列已存在")

conn.close()
