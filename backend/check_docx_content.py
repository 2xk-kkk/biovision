import sys
sys.path.insert(0, '.')
from service.parse_special_training import read_docx_content

elements = read_docx_content('D:/biology/走进细胞 全章节专项练习题（2小节·每题15道·含详细解析）.docx')

for i, elem in enumerate(elements[:80]):
    text = elem['text'].strip()
    if text:
        print(f"{i}: {text[:100]}")
