import sys
sys.path.insert(0, 'service')
from extract_questions import read_docx_content, build_image_mapping, extract_images
import re

docx_path = 'uploads/exams/25云南/2025年高考生物试卷（云南卷）.docx'

extract_images(docx_path, '25云南')
image_mapping = build_image_mapping(docx_path, '25云南')
paragraphs = read_docx_content(docx_path)

start_index = 0
for i, para in enumerate(paragraphs):
    if '选择题' in para['text']:
        start_index = i + 1
        break

question_starts = []
for i, para in enumerate(paragraphs[start_index:]):
    line = para['text'].strip()
    q_num_match = re.match(r'^(\d{1,3})[\.．、]\s*(.+)$', line)
    if q_num_match:
        question_starts.append(i)

print(f"选择题从段落 {start_index} 开始")
print(f"题目边界: {question_starts}")

for idx in range(min(12, len(question_starts))):
    start = question_starts[idx]
    end = question_starts[idx + 1] if idx + 1 < len(question_starts) else len(paragraphs[start_index:])
    
    all_paragraphs = paragraphs[start_index:][start:end]
    
    q_num_match = re.match(r'^(\d{1,3})[\.．、]\s*(.+)$', all_paragraphs[0]['text'].strip())
    if not q_num_match:
        continue
    
    question_num = int(q_num_match.group(1))
    question = {
        'number': question_num,
        'stem': q_num_match.group(2),
        'options': {'A': '', 'B': '', 'C': '', 'D': ''},
        'answer': '',
        'images': []
    }
    
    has_image_ref = '图' in question['stem']
    current_option = None
    
    for para in all_paragraphs[1:]:
        line = para['text'].strip()
        
        if line.startswith('第') and '页' in line:
            continue
        
        if '图' in line:
            has_image_ref = True
        
        option_pattern = re.compile(r'([A-D])[\.\uff0e、]\s*(.+?)(?=\s*[A-D][\.\uff0e、]|$)')
        option_matches = option_pattern.findall(line)
        if option_matches:
            for opt_key, opt_text in option_matches:
                if opt_key in question['options']:
                    question['options'][opt_key] = opt_text.strip()
                    current_option = opt_key
            continue
        
        answer_match = re.match(r'^答案[\uff1a:]\s*([A-D])', line)
        if answer_match:
            question['answer'] = answer_match.group(1)
            continue
        
        answer_match2 = re.search(r'答案[\uff1a:]\s*([A-D])', line)
        if answer_match2:
            question['answer'] = answer_match2.group(1)
            continue
        
        if line.startswith(tuple('ABCD')):
            opt_key = line[0]
            rest = line[1:].lstrip('.．、').strip()
            if opt_key in question['options']:
                question['options'][opt_key] = rest
                current_option = opt_key
        elif current_option and line:
            question['options'][current_option] += ' ' + line
        elif not line.startswith(tuple('ABCD')) and not line.startswith('答案') and line:
            if not question['stem'].endswith('。') and not question['stem'].endswith('？') and not question['stem'].endswith('）'):
                question['stem'] += ' ' + line
    
    print(f"\n=== 第{question_num}题 ===")
    print(f"范围: 偏移 [{start}, {end}), 绝对段落 [{start_index + start}, {start_index + end})")
    print(f"题目内容开头: {question['stem'][:50]}")
    print(f"包含图引用: {has_image_ref}")
    
    print("\n扫描段落中的图片:")
    for j, para in enumerate(all_paragraphs):
        abs_idx = start_index + start + j
        if para['images']:
            print(f"  相对{j} (绝对{abs_idx}): {len(para['images'])}张图片 - {para['images']}")
            for img_id in para['images']:
                if img_id in image_mapping:
                    print(f"    -> {image_mapping[img_id]}")
                else:
                    print(f"    -> 未找到映射")
    
    print("\n关联图片:")
    for para in all_paragraphs:
        if para['images']:
            for img_id in para['images']:
                if img_id in image_mapping:
                    img_path = image_mapping[img_id]
                    if img_path not in question['images']:
                        question['images'].append(img_path)
                        print(f"  关联图片: {img_path}")
    
    print(f"\n最终结果: 第{question_num}题有 {len(question['images'])} 张图片")