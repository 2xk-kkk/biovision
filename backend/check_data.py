import sqlite3
import json

conn = sqlite3.connect('forum.db')
c = conn.cursor()

# Check sample data
c.execute("SELECT id, name, question_count FROM exams WHERE name LIKE '%大庆%'")
print("=== 大庆中学 exams ===")
for r in c.fetchall():
    print(f"  id={r[0]}, name={r[1]}, questions={r[2]}")

# Check all exam names
c.execute("SELECT id, name FROM exams WHERE question_count > 0 ORDER BY id DESC LIMIT 30")
print("\n=== All exam names ===")
for r in c.fetchall():
    print(f"  id={r[0]}, name={r[1]}")

# Pick one exam to check questions
c.execute("SELECT id, name FROM exams WHERE name LIKE '%大庆%' LIMIT 1")
exam = c.fetchone()
if exam:
    print(f"\n=== Questions for {exam[1]} (id={exam[0]}) ===")
    c.execute("SELECT number, stem, option_a, images, type FROM questions WHERE exam_id = ? ORDER BY number LIMIT 5", (exam[0],))
    for r in c.fetchall():
        print(f"  Q{r[0]}: stem={r[1][:80]}...")
        print(f"    images={r[3]}, type={r[4]}")
        if r[3]:
            try:
                imgs = json.loads(r[3])
                print(f"    parsed images: {imgs}")
            except:
                pass

# Check for image storage across all exams
c.execute("SELECT id FROM exams WHERE question_count > 0")
all_exams = c.fetchall()
has_images = 0
no_images = 0
for (exam_id,) in all_exams:
    c.execute("SELECT COUNT(*) FROM questions WHERE exam_id = ? AND images IS NOT NULL AND images != '' AND images != '[]'", (exam_id,))
    count = c.fetchone()[0]
    if count > 0:
        has_images += 1
    else:
        no_images += 1
print(f"\nExams with images: {has_images}, without: {no_images}")

# Check actual file system for images
import os
exam_dir = r'D:\paper'
if os.path.exists(exam_dir):
    print("\n=== Files in D:\\paper ===")
    for folder in os.listdir(exam_dir):
        folder_path = os.path.join(exam_dir, folder)
        if os.path.isdir(folder_path):
            images = [f for f in os.listdir(folder_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.bmp'))]
            if images:
                print(f"  {folder}: {len(images)} images - {images[:3]}")

conn.close()