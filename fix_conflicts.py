import re

files = [
    'frontend/practice/exams.html',
    'frontend/practice/quiz.html'
]

for file_path in files:
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    content = re.sub(r'<<<<<<< HEAD\n.*?=======\n.*?>>>>>>> [0-9a-f]+\n', '', content, flags=re.DOTALL)
    content = re.sub(r'<<<<<<< HEAD\n', '', content)
    content = re.sub(r'=======\n', '', content)
    content = re.sub(r'>>>>>>> [0-9a-f]+\n', '', content)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f'修复完成: {file_path}')

print('所有文件已修复')