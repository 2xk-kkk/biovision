import sqlite3

conn = sqlite3.connect('backend/database/forum.db')
cursor = conn.cursor()

# 检查post_image表中的数据
cursor.execute('SELECT * FROM post_image LIMIT 10')
print("post_image表中的数据：")
for row in cursor.fetchall():
    print(row)

conn.close()