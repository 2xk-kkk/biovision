import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUESTIONS_FILE = os.path.join(BASE_DIR, 'backend', 'questions.json')
EXAM_IMAGES_DIR = os.path.join(BASE_DIR, 'backend', 'uploads', 'exam_images')

with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=== 检查云南卷原始数据 ===")

for key in data.keys():
    if '云南' in key or 'yunnan' in key.lower():
        print(f"\n找到键: {key}")
        exam_data = data[key]
        questions = exam_data['questions']
        print(f"题目数: {len(questions)}")
        
        print("\n各题目的图片:")
        for q in questions:
            images = q.get('images', [])
            if images:
                print(f"  题目 {q['number']}: {images}")
                
                for img_path in images:
                    img_filename = os.path.basename(img_path)
                    print(f"    文件: {img_filename}")

print("\n=== 检查实际图片目录 ===")
for dir_name in os.listdir(EXAM_IMAGES_DIR):
    if '云南' in dir_name:
        dir_path = os.path.join(EXAM_IMAGES_DIR, dir_name)
        files = sorted(os.listdir(dir_path))
        print(f"\n{dir_name}:")
        for f in files:
            print(f"  {f}")