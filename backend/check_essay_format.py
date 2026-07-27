import sys
sys.path.insert(0, '.')
from service.parse_special_training import read_docx_content

elements = read_docx_content('D:/biology/走进细胞 全章节专项练习题（2小节·每题15道·含详细解析）.docx')

print("=== 大题部分 ===")
for i, elem in enumerate(elements):
    text = elem['text'].strip()
    if text and ('三、' in text or '简答题' in text or text.startswith('1.') or text.startswith('答案解析')):
        print(f"{i}: {text[:150]}")
