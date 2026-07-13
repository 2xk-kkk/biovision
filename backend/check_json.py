import json
with open('questions.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for exam_name, exam_data in data.items():
    for q in exam_data['questions']:
        if 'images' in q:
            print(f"{exam_name} Q{q['number']}: {type(q['images'])} = {repr(q['images'])}")
            break