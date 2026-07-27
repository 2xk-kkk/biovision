import json
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUESTIONS_FILE = os.path.join(BASE_DIR, 'backend', 'questions.json')
EXAM_IMAGES_DIR = os.path.join(BASE_DIR, 'backend', 'uploads', 'exam_images')
DB_FILE = os.path.join(BASE_DIR, 'backend', 'forum.db')

name_mapping = {
    '25云南': '2025_云南卷_生物',
    '25全国卷': '2025_全国卷_生物',
    '25四川': '2025_四川卷_生物',
    '25山东': '2025_山东卷_生物',
    '25浙江1月': '2025_浙江1月卷_生物',
    '25重庆': '2025_重庆卷_生物',
    '25陕西青宁': '2025_陕晋青宁卷_生物',
}

with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()

print("=== 恢复原始图片映射 ===")

for json_name, exam_data in data.items():
    db_name = name_mapping.get(json_name, json_name)
    
    cursor.execute('SELECT id FROM exams WHERE name = ?', (db_name,))
    result = cursor.fetchone()
    if not result:
        continue
    exam_id = result[0]
    
    exam_images_dir = os.path.join(EXAM_IMAGES_DIR, json_name)
    if not os.path.exists(exam_images_dir):
        exam_images_dir = os.path.join(EXAM_IMAGES_DIR, db_name)
        if not os.path.exists(exam_images_dir):
            cursor.execute('UPDATE questions SET images = ? WHERE exam_id = ?', ('[]', exam_id))
            print(f"{db_name}: 无图片目录")
            conn.commit()
            continue
    
    print(f"\n{db_name}:")
    
    questions = exam_data['questions']
    for q in questions:
        q_num = q['number']
        original_images = q.get('images', [])
        
        valid_images = []
        for img_path in original_images:
            img_filename = os.path.basename(img_path)
            full_path = os.path.join(exam_images_dir, img_filename)
            
            if os.path.exists(full_path) and img_filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                valid_images.append(img_path)
        
        if valid_images:
            cursor.execute('UPDATE questions SET images = ? WHERE exam_id = ? AND number = ?', 
                          (json.dumps(valid_images), exam_id, q_num))
            print(f"  题目 {q_num}: {valid_images}")
        else:
            cursor.execute('UPDATE questions SET images = ? WHERE exam_id = ? AND number = ?', 
                          ('[]', exam_id, q_num))
    
    conn.commit()

conn.close()
print("\n=== 完成 ===")