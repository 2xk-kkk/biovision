import zipfile
import xml.etree.ElementTree as ET
import os
import re
import json

NSMAP = {
    'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
    'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships',
    'v': 'urn:schemas-microsoft-com:vml'
}

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
UPLOAD_DIR = os.path.join(BASE_DIR, 'uploads')
IMAGE_OUTPUT_DIR = os.path.join(UPLOAD_DIR, 'exam_images')

def extract_images(docx_path, exam_name):
    exam_image_dir = os.path.join(IMAGE_OUTPUT_DIR, exam_name)
    os.makedirs(exam_image_dir, exist_ok=True)
    
    with zipfile.ZipFile(docx_path, 'r') as z:
        for name in z.namelist():
            if name.startswith('word/media/') and name != 'word/media/':
                img_num = re.search(r'image(\d+)', name)
                if img_num:
                    ext = os.path.splitext(name)[1]
                    new_name = f"img{img_num.group(1)}{ext}"
                else:
                    new_name = os.path.basename(name)
                dest_path = os.path.join(exam_image_dir, new_name)
                with z.open(name) as src, open(dest_path, 'wb') as dst:
                    dst.write(src.read())

def build_image_mapping(docx_path, exam_name):
    mapping = {}
    with zipfile.ZipFile(docx_path, 'r') as z:
        if 'word/_rels/document.xml.rels' in z.namelist():
            with z.open('word/_rels/document.xml.rels') as f:
                tree = ET.parse(f)
                root = tree.getroot()
                ns = {'r': 'http://schemas.openxmlformats.org/package/2006/relationships'}
                
                image_counter = {}
                for rel in root.iter('{' + ns['r'] + '}Relationship'):
                    rid = rel.get('Id')
                    target = rel.get('Target')
                    if target and target.startswith('media/'):
                        img_num = re.search(r'image(\d+)', target)
                        if img_num:
                            num = int(img_num.group(1))
                            ext = os.path.splitext(target)[1]
                            img_name = f"img{num}{ext}"
                        else:
                            img_name = os.path.basename(target)
                        web_path = f"/uploads/exam_images/{exam_name}/{img_name}"
                        mapping[rid] = web_path
    return mapping

def parse_table(tbl):
    table_text = '\n'
    for tr in tbl.iter('{' + NSMAP['w'] + '}tr'):
        row_cells = []
        for tc in tr.iter('{' + NSMAP['w'] + '}tc'):
            cell_text = ''
            for t in tc.iter('{' + NSMAP['w'] + '}t'):
                if t.text:
                    cell_text += t.text
            row_cells.append(cell_text)
        table_text += ' | '.join(row_cells) + '\n'
    return table_text

def read_docx_content(docx_path):
    elements = []
    with zipfile.ZipFile(docx_path, 'r') as z:
        if 'word/document.xml' not in z.namelist():
            return []
        
        with z.open('word/document.xml') as f:
            tree = ET.parse(f)
            root = tree.getroot()
            
            body = None
            for child in root:
                if child.tag == '{' + NSMAP['w'] + '}body':
                    body = child
                    break
            
            if not body:
                return []
            
            for child in body:
                if child.tag == '{' + NSMAP['w'] + '}p':
                    text_content = ''
                    images = []
                    
                    for run in child.iter('{' + NSMAP['w'] + '}r'):
                        for t in run.iter('{' + NSMAP['w'] + '}t'):
                            if t.text:
                                text_content += t.text
                    
                    for pict in child.iter('{' + NSMAP['w'] + '}pict'):
                        for imagedata in pict.iter('{' + NSMAP['v'] + '}imagedata'):
                            rid = imagedata.get('{' + NSMAP['r'] + '}id')
                            if rid:
                                images.append(rid)
                    
                    for drawing in child.iter('{' + NSMAP['w'] + '}drawing'):
                        for blip in drawing.iter():
                            if 'blip' in blip.tag:
                                embed = blip.get('{' + NSMAP['r'] + '}embed')
                                if embed:
                                    images.append(embed)
                    
                    elements.append({
                        'type': 'paragraph',
                        'text': text_content,
                        'images': images
                    })
                
                elif child.tag == '{' + NSMAP['w'] + '}tbl':
                    table_text = parse_table(child)
                    elements.append({
                        'type': 'table',
                        'text': table_text,
                        'images': []
                    })
    
    return elements

def is_question_number(line):
    match = re.match(r'^(\d{1,3})[\.．、]\s*(.+)$', line.strip())
    return match

def is_page_number(line):
    return line.strip().startswith('第') and '页' in line.strip()

def is_answer_section(line):
    text = line.strip()
    return text.startswith('参考答案') or text.startswith('参考答案及评分标准') or text.startswith('答案及解析') or '参考答案' in text or '答案：' in text or text.startswith('【答案】') and '题答案' not in text

def is_instruction(line):
    text = line.strip()
    keywords = ['选择题必须使用', '非选择题必须使用', '作图可先使用', '保持卡面清洁', '不要折叠', '不要弄破', '不准使用', '修改液', '修正带', '刮纸刀', '答题前', '考生须知', '注意事项']
    return any(keyword in text for keyword in keywords)

def is_fill_question(stem):
    return '____' in stem or re.search(r'（\d+）', stem) or re.search(r'\(\d+\)', stem)

def parse_questions(docx_path, exam_name):
    extract_images(docx_path, exam_name)
    image_mapping = build_image_mapping(docx_path, exam_name)
    elements = read_docx_content(docx_path)
    
    answers = {}
    current_answer_num = None
    for elem in elements:
        if elem['type'] == 'paragraph':
            text = elem['text'].strip()
            num_match = re.search(r'【(\d+)题答案】', text)
            if num_match:
                current_answer_num = int(num_match.group(1))
            
            ans_match = re.match(r'【答案】\s*(.+)$', text)
            if ans_match and current_answer_num:
                answers[current_answer_num] = ans_match.group(1).strip()
                current_answer_num = None
    
    start_index = 0
    found_choice_title = False
    for i, elem in enumerate(elements):
        if elem['type'] == 'paragraph':
            text = elem['text'].strip()
            if text.startswith('一、') and ('选择题' in text or '单项选择' in text):
                start_index = i + 1
                found_choice_title = True
                break
    
    if not found_choice_title:
        for i, elem in enumerate(elements):
            if elem['type'] == 'paragraph':
                match = is_question_number(elem['text'])
                if match and int(match.group(1)) == 1:
                    start_index = i
                    break
    
    header_images = set()
    for elem in elements[:start_index]:
        for img_id in elem['images']:
            header_images.add(img_id)
    
    question_boundaries = []
    found_first = False
    expected_num = 1
    
    for i, elem in enumerate(elements[start_index:]):
        if elem['type'] == 'paragraph':
            text = elem['text'].strip()
            
            if is_instruction(text):
                continue
            
            match = is_question_number(elem['text'])
            if match:
                num = int(match.group(1))
                if not found_first:
                    if num == 1:
                        found_first = True
                        question_boundaries.append(i)
                        expected_num = 2
                else:
                    if num == expected_num or num == expected_num + 1:
                        question_boundaries.append(i)
                        expected_num = num + 1
    
    questions = []
    
    for idx in range(len(question_boundaries)):
        start = question_boundaries[idx]
        end = question_boundaries[idx + 1] if idx + 1 < len(question_boundaries) else len(elements[start_index:])
        
        question_elements = elements[start_index:][start:end]
        
        q_num_match = is_question_number(question_elements[0]['text'])
        if not q_num_match:
            continue
        
        question_num = int(q_num_match.group(1))
        stem_text = q_num_match.group(2)
        options = {'A': '', 'B': '', 'C': '', 'D': ''}
        answer = ''
        images = []
        current_option = None
        found_option = False
        is_fill = is_fill_question(stem_text)
        
        for elem in question_elements[1:]:
            line = elem['text'].strip()
            
            if is_page_number(line):
                for img_id in elem['images']:
                    if img_id not in header_images and img_id in image_mapping:
                        img_path = image_mapping[img_id]
                        if img_path not in images:
                            images.append(img_path)
                continue
            
            if '选择题' in line or '非选择题' in line:
                continue
            
            for img_id in elem['images']:
                if img_id not in header_images and img_id in image_mapping:
                    img_path = image_mapping[img_id]
                    if img_path not in images:
                        images.append(img_path)
            
            if elem['type'] == 'table':
                stem_text += '\n' + elem['text']
                continue
            
            if is_fill:
                if line:
                    stem_text += '\n' + line
                continue
            
            option_pattern = re.compile(r'^([A-D])[\.\uff0e、]\s+')
            multi_option_pattern = re.compile(r'([A-D])[\.\uff0e、]\s+')
            
            if option_pattern.match(line):
                found_option = True
                opt_key = line[0]
                rest = line[1:].lstrip('.．、').strip()
                
                matches = multi_option_pattern.findall(line)
                if len(matches) > 1:
                    parts = multi_option_pattern.split(line)
                    parts = [p.strip() for p in parts if p.strip()]
                    for i in range(0, len(parts), 2):
                        if i + 1 < len(parts):
                            opt_key_part = parts[i]
                            opt_val_part = parts[i + 1]
                            if opt_key_part in options:
                                options[opt_key_part] = opt_val_part
                                current_option = opt_key_part
                else:
                    if opt_key in options:
                        options[opt_key] = rest
                        current_option = opt_key
            elif found_option and line.startswith(tuple('ABCD')):
                opt_key = line[0]
                rest = line[1:].lstrip('.．、').strip()
                if opt_key in options:
                    options[opt_key] = rest
                    current_option = opt_key
            elif found_option and current_option and line:
                options[current_option] += ' ' + line
            elif not found_option and line:
                if line.startswith('（') or line.startswith('('):
                    stem_text += '\n' + line
                elif stem_text.endswith('。') or stem_text.endswith('？') or stem_text.endswith('）'):
                    stem_text += '\n' + line
                else:
                    stem_text += ' ' + line
        
        has_options = any(options[k] for k in options)
        if question_num in answers:
            answer = answers[question_num]
        
        questions.append({
            'number': question_num,
            'stem': stem_text,
            'options': options,
            'answer': answer,
            'images': images,
            'type': 'non_choice' if not has_options else 'choice'
        })
    
    return questions

def find_docx_file(dir_path):
    for item in os.listdir(dir_path):
        item_path = os.path.join(dir_path, item)
        if item.endswith('.docx'):
            return item_path
        elif os.path.isdir(item_path):
            found = find_docx_file(item_path)
            if found:
                return found
    return None

def extract_all_exams(exam_dir):
    os.makedirs(IMAGE_OUTPUT_DIR, exist_ok=True)
    all_results = {}
    
    for exam_name in os.listdir(exam_dir):
        exam_path = os.path.join(exam_dir, exam_name)
        if os.path.isdir(exam_path):
            docx_path = find_docx_file(exam_path)
            if docx_path:
                questions = parse_questions(docx_path, exam_name)
                all_results[exam_name] = {
                    'exam_name': exam_name,
                    'question_count': len(questions),
                    'questions': questions
                }
                img_count = sum(1 for q in questions if q['images'])
                print(f"成功提取 {exam_name}: {len(questions)} 道题，{img_count} 道题有图片")
    
    output_path = os.path.join(BASE_DIR, 'questions.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    
    print(f"\n提取结果已保存到: {output_path}")
    print(f"共提取 {len(all_results)} 套试卷")
    return all_results

if __name__ == '__main__':
    exam_dir = os.path.join(BASE_DIR, 'uploads', 'exams')
    extract_all_exams(exam_dir)