import sys
sys.path.insert(0, '.')
from service.parse_special_training import read_docx_content

elements = read_docx_content('D:/biology/走进细胞 全章节专项练习题（2小节·每题15道·含详细解析）.docx')

print("=== 搜索这道题的上下文 ===")
for i, elem in enumerate(elements):
    text = elem['text'].strip()
    if text and ('简述高等动物' in text or text.startswith('二、') or text.startswith('三、')):
        print(f"{i}: {text[:150]}")
        # 显示前后几行
        for j in range(max(0, i-2), min(len(elements), i+3)):
            if j != i:
                print(f"  {j}: {elements[j]['text'][:80]}")
        print()
