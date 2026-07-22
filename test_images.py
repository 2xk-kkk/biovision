import os

image_base = r'd:\15821\biovision\uploads\exam_images'
print("exam_images目录下的文件夹:")
for folder in os.listdir(image_base):
    folder_path = os.path.join(image_base, folder)
    if os.path.isdir(folder_path):
        file_count = len(os.listdir(folder_path))
        print(f"  {folder} - {file_count}个文件")

print("\n--- 检查数据库中的图片路径对应的文件是否存在 ---")
import sqlite3
db = sqlite3.connect('backend/forum.db')
cursor = db.cursor()

cursor.execute('SELECT id, name FROM exams WHERE id = 103')
exam = cursor.fetchone()
print(f"\n试卷ID 103: {exam[1]}")

cursor.execute('SELECT number, images FROM questions WHERE exam_id = 103 AND images != "" AND images != "[]" LIMIT 5')
for q in cursor.fetchall():
    import json
    images = json.loads(q[1])
    for img_path in images:
        full_path = os.path.join(r'd:\15821\biovision', img_path.lstrip('/'))
        exists = os.path.exists(full_path)
        print(f"  第{q[0]}题: {img_path} -> {'存在' if exists else '不存在'}")

db.close()