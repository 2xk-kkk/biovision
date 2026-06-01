import sqlite3
import os
import shutil

db_path = 'c:/Users/Vivian/biovision/backend/forum.db'
uploads_dir = 'c:/Users/Vivian/biovision/uploads'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 备份数据库
backup_path = db_path + '.backup_' + str(os.path.getsize(db_path))
shutil.copy(db_path, backup_path)
print(f"已备份数据库到 {backup_path}")

# 检查所有文件URL
cursor.execute('SELECT id, post_id, image_url, sort_order, create_at FROM post_image WHERE image_url LIKE "%uploads%"')
all_rows = cursor.fetchall()

print(f"\n数据库中总共有 {len(all_rows)} 个文件URL")

missing_files = []
existing_files = []

for row in all_rows:
    file_url = row[2]
    file_name = os.path.basename(file_url)
    file_path = os.path.join(uploads_dir, file_name)
    exists = os.path.exists(file_path)
    if exists:
        existing_files.append(row)
    else:
        missing_files.append(row)
        print(f"文件不存在: ID: {row[0]}, post_id: {row[1]}, URL: {file_url}")

print()
print(f"存在的文件: {len(existing_files)}")
print(f"不存在的文件: {len(missing_files)}")

# 删除不存在的文件记录
if missing_files:
    print()
    print("正在删除不存在的文件记录...")
    for row in missing_files:
        cursor.execute('DELETE FROM post_image WHERE id = ?', (row[0],))
    conn.commit()
    print(f"已删除 {len(missing_files)} 条记录")

conn.close()
print("\n完成！")