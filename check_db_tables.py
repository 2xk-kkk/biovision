import sqlite3
import os
import shutil

db_path = 'c:/Users/Vivian/biovision/backend/forum.db'
uploads_dir = 'c:/Users/Vivian/biovision/uploads'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 检查表名
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("数据库中的表:")
for table in tables:
    print(f"  - {table[0]}")

# 获取post_image表的结构
cursor.execute("PRAGMA table_info(post_image)")
columns = cursor.fetchall()
print("\npost_image表的结构:")
for col in columns:
    print(f"  - {col[1]}: {col[2]}")

# 检查所有文件URL
cursor.execute('SELECT id, image_url FROM post_image WHERE image_url LIKE "%uploads%"')
all_rows = cursor.fetchall()

print(f"\n数据库中总共有 {len(all_rows)} 个文件URL")

missing_files = []
existing_files = []

for row in all_rows:
    file_url = row[1]
    file_name = os.path.basename(file_url)
    file_path = os.path.join(uploads_dir, file_name)
    exists = os.path.exists(file_path)
    if exists:
        existing_files.append(row)
    else:
        missing_files.append(row)
        print(f"文件不存在: ID: {row[0]}, URL: {file_url}")

print()
print(f"存在的文件: {len(existing_files)}")
print(f"不存在的文件: {len(missing_files)}")

conn.close()