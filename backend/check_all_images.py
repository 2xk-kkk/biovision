import json

with open('questions.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for exam_name, exam_data in data.items():
    print(f"\n=== {exam_name} ===")
    for q in exam_data['questions']:
        if q['images']:
            print(f"第{q['number']}题: {len(q['images'])}张图片 - {q['images']}")