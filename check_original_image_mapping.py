import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
QUESTIONS_FILE = os.path.join(BASE_DIR, 'backend', 'questions.json')

with open(QUESTIONS_FILE, 'r', encoding='utf-8') as f:
    data = json.load(f)

print("=== 检查原始questions.json中的图片分配 ===")

for exam_name, exam_data in list(data.items())[:3]:
    questions = exam_data['questions']
    print(f"\n{exam_name}:")
    for q in questions:
        images = q.get('images', [])
        if images:
            print(f"  题目 {q['number']}: {images}")