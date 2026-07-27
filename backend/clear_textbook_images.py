import sqlite3

conn = sqlite3.connect('forum.db')
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM questions WHERE textbook IS NOT NULL AND textbook != ''")
count = cursor.fetchone()[0]
print(f"章节练习题总数: {count}")

cursor.execute("SELECT COUNT(*) FROM questions WHERE textbook IS NOT NULL AND textbook != '' AND images != '[]'")
img_count = cursor.fetchone()[0]
print(f"有图片的章节练习题数: {img_count}")

cursor.execute("UPDATE questions SET images = '[]' WHERE textbook IS NOT NULL AND textbook != ''")
conn.commit()

cursor.execute("SELECT COUNT(*) FROM questions WHERE textbook IS NOT NULL AND textbook != '' AND images != '[]'")
after_count = cursor.fetchone()[0]
print(f"清理后有图片的章节练习题数: {after_count}")

print("章节练习题图片已清除")

conn.close()