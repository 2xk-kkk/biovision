import sys
sys.path.insert(0, 'service')
from extract_questions import read_docx_content

docx_path = 'uploads/exams/25云南/2025年高考生物试卷（云南卷）.docx'
paragraphs = read_docx_content(docx_path)

start_index = 0
for i, para in enumerate(paragraphs):
    if '选择题' in para['text']:
        start_index = i + 1
        print(f"选择题标题在段落 {i}")
        break

print(f"\n从段落 {start_index} 开始解析题目")

question_starts = []
for i, para in enumerate(paragraphs[start_index:]):
    line = para['text'].strip()
    if line.startswith(tuple('一二三四五六七八九十')) and ('题' in line or '、' in line):
        continue
    if line.startswith('第') and '页' in line:
        continue
    import re
    q_num_match = re.match(r'^(\d{1,3})[\.．、]\s*(.+)$', line)
    if q_num_match:
        question_starts.append(i)
        print(f"题目 {q_num_match.group(1)} 在偏移 {i} (绝对段落 {start_index + i})")

print(f"\n题目边界: {question_starts}")

for idx in range(min(6, len(question_starts))):
    start = question_starts[idx]
    end = question_starts[idx + 1] if idx + 1 < len(question_starts) else len(paragraphs[start_index:])
    print(f"\n第{idx+1}题: 偏移范围 [{start}, {end}), 绝对段落 [{start_index + start}, {start_index + end})")
    all_paragraphs = paragraphs[start_index:][start:end]
    for j, para in enumerate(all_paragraphs):
        abs_idx = start_index + start + j
        text_display = para['text'][:40] if len(para['text']) > 40 else para['text']
        has_img = '有图片' if para['images'] else '无图片'
        print(f"  相对{j} (绝对{abs_idx}): {has_img} - '{text_display}'")