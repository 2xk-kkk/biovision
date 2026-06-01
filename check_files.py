import sqlite3
import os

db_path = 'c:/Users/Vivian/biovision/backend/forum.db'
uploads_dir = 'c:/Users/Vivian/biovision/uploads'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute('SELECT id, image_url FROM post_image WHERE image_url LIKE "%uploads%" LIMIT 20')
rows = cursor.fetchall()

print(f"数据库中的文件URL (共 {len(rows)} 条):")
for row in rows:
    file_url = row[1]
    file_name = os.path.basename(file_url)
    file_path = os.path.join(uploads_dir, file_name)
    exists = os.path.exists(file_path)
    print(f"  ID: {row[0]}, URL: {file_url}, 文件存在: {exists}")

conn.close()