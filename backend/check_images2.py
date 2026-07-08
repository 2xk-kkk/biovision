import json
with open('questions.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
for q in data['25云南']['questions'][:6]:
    print(f'第{q["number"]}题: {len(q["images"])}张图片 - {q["images"]}')