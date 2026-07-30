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

import sys
sys.path.insert(0, BASE_DIR)
from database.db import get_db_connection

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
                    
                    for run in child.iter('{' + NSMAP['w'] + '}r'):
                        for t in run.iter('{' + NSMAP['w'] + '}t'):
                            if t.text:
                                text_content += t.text
                    
                    elements.append({
                        'type': 'paragraph',
                        'text': text_content,
                        'images': []
                    })
                
                elif child.tag == '{' + NSMAP['w'] + '}tbl':
                    table_text = ''
                    for tr in child.iter('{' + NSMAP['w'] + '}tr'):
                        row_cells = []
                        for tc in tr.iter('{' + NSMAP['w'] + '}tc'):
                            cell_text = ''
                            for t in tc.iter('{' + NSMAP['w'] + '}t'):
                                if t.text:
                                    cell_text += t.text
                            row_cells.append(cell_text)
                        table_text += ' | '.join(row_cells) + '\n'
                    elements.append({
                        'type': 'table',
                        'text': table_text,
                        'images': []
                    })
    return elements

def is_question_number(line):
    match = re.match(r'^(\d{1,3})[\.．、]\s*(.+)$', line.strip())
    return match

def detect_question_type(stem, options):
    has_options = any(options[k] for k in options)
    
    if has_options:
        if len([k for k in options if options[k]]) >= 4:
            return 'choice'
        return 'choice'
    
    if '____' in stem or re.search(r'（\d+）', stem) or re.search(r'\(\d+\)', stem):
        return 'fill'
    
    return 'essay'

def parse_special_training(docx_path):
    elements = read_docx_content(docx_path)
    
    questions = []
    current_section = ''
    current_type = ''
    current_question = None
    
    for elem in elements:
        text = elem['text'].strip()
        
        if not text:
            continue
        
        if text.startswith('一、') and '选择题' in text:
            current_type = 'choice'
            continue
        elif text.startswith('二、') and '填空题' in text:
            current_type = 'fill'
            continue
        elif text.startswith('三、') and ('大题' in text or '简答题' in text):
            current_type = 'essay'
            continue
        
        match = is_question_number(text)
        if match:
            if current_question:
                questions.append(current_question)
            
            num = int(match.group(1))
            stem_text = match.group(2)
            current_question = {
                'number': num,
                'stem': stem_text,
                'options': {'A': '', 'B': '', 'C': '', 'D': ''},
                'answer': '',
                'analysis': '',
                'type': current_type
            }
        elif current_question:
            option_pattern = re.compile(r'([A-D])[\.\uff0e、]\s+')
            matches = option_pattern.findall(text)
            
            if len(matches) == 1 and option_pattern.match(text):
                opt_key = matches[0]
                rest = text[1:].lstrip('.．、').strip()
                current_question['options'][opt_key] = rest
            elif len(matches) >= 2:
                parts = re.split(r'([A-D])[\.\uff0e、]\s+', text)
                parts = [p.strip() for p in parts if p.strip()]
                for i in range(0, len(parts), 2):
                    if i + 1 < len(parts):
                        key = parts[i]
                        value = parts[i + 1]
                        if key in ['A', 'B', 'C', 'D']:
                            current_question['options'][key] = value
            elif text.startswith('答案：') or text.startswith('答案:') or text.startswith('【答案】'):
                current_question['answer'] = text.replace('答案：', '').replace('答案:', '').replace('【答案】', '').strip()
            elif text.startswith('解析：') or text.startswith('解析:') or text.startswith('【解析】'):
                current_question['analysis'] = text.replace('解析：', '').replace('解析:', '').replace('【解析】', '').strip()
            elif text.startswith('答案解析：') or text.startswith('答案解析:') or text.startswith('【答案解析】'):
                content = text.replace('答案解析：', '').replace('答案解析:', '').replace('【答案解析】', '').strip()
                if current_question['type'] == 'essay':
                    current_question['answer'] = content
                    current_question['analysis'] = content
                else:
                    current_question['analysis'] = content
            elif not current_question['answer']:
                answer_match = re.match(r'^([ABCDabcd]+)$', text.strip())
                if answer_match:
                    current_question['answer'] = text.strip().upper()
                elif text.startswith('【答案】'):
                    current_question['answer'] = text.replace('【答案】', '').strip()
                elif text.startswith('答案：') or text.startswith('答案:'):
                    current_question['answer'] = text.replace('答案：', '').replace('答案:', '').strip()
                else:
                    current_question['stem'] += ' ' + text
    
    if current_question:
        questions.append(current_question)
    
    for q in questions:
        if not q['type']:
            q['type'] = detect_question_type(q['stem'], q['options'])
    
    choice_count = 0
    fill_count = 0
    essay_count = 0
    
    for q in questions:
        if q['type'] == 'choice':
            choice_count += 1
            q['number'] = choice_count
        elif q['type'] == 'fill':
            fill_count += 1
            q['number'] = fill_count
        elif q['type'] == 'essay':
            essay_count += 1
            q['number'] = essay_count
    
    return questions

def insert_questions_to_db(docx_path):
    questions = parse_special_training(docx_path)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(questions)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'textbook' not in columns:
        cursor.execute("ALTER TABLE questions ADD COLUMN textbook TEXT")
    if 'chapter' not in columns:
        cursor.execute("ALTER TABLE questions ADD COLUMN chapter TEXT")
    if 'section' not in columns:
        cursor.execute("ALTER TABLE questions ADD COLUMN section TEXT")
    if 'type' not in columns:
        cursor.execute("ALTER TABLE questions ADD COLUMN type TEXT")
    
    conn.commit()
    
    filename = os.path.basename(docx_path)
    
    textbook = '必修一：分子与细胞'
    chapter = '第1章 走近细胞'
    section = '专项训练'
    
    chapter_map = {
        '组成细胞的分子': ('必修一：分子与细胞', '第2章 组成细胞的分子'),
        '细胞的基本结构': ('必修一：分子与细胞', '第3章 细胞的基本结构'),
        '细胞的物质输入和输出': ('必修一：分子与细胞', '第4章 细胞的物质输入和输出'),
        '细胞的能量供应和利用': ('必修一：分子与细胞', '第5章 细胞的能量供应和利用'),
        '细胞的生命历程': ('必修一：分子与细胞', '第6章 细胞的生命历程'),
        '遗传因子的发现': ('必修二：遗传与进化', '第1章 遗传因子的发现'),
        '基因和染色体的关系': ('必修二：遗传与进化', '第2章 基因和染色体的关系'),
        '基因的本质': ('必修二：遗传与进化', '第3章 基因的本质'),
        '基因的表达': ('必修二：遗传与进化', '第4章 基因的表达'),
        '基因突变及其他变异': ('必修二：遗传与进化', '第5章 基因突变及其他变异'),
        '生物的进化': ('必修二：遗传与进化', '第6章 生物的进化'),
        '人体的内环境与稳态': ('选择性必修一：稳态与调节', '第1章 人体的内环境与稳态'),
        '神经调节': ('选择性必修一：稳态与调节', '第2章 神经调节'),
        '体液调节': ('选择性必修一：稳态与调节', '第3章 体液调节'),
        '免疫调节': ('选择性必修一：稳态与调节', '第4章 免疫调节'),
        '植物生命活动的调节': ('选择性必修一：稳态与调节', '第5章 植物生命活动的调节'),
        '种群及其动态': ('选择性必修二：生物与环境', '第1章 种群及其动态'),
        '群落及其演替': ('选择性必修二：生物与环境', '第2章 群落及其演替'),
        '生态系统及其稳定性': ('选择性必修二：生物与环境', '第3章 生态系统及其稳定性'),
        '人与环境': ('选择性必修二：生物与环境', '第4章 人与环境'),
        '基因工程': ('选择性必修三：生物技术与工程', '第1章 基因工程'),
        '细胞工程': ('选择性必修三：生物技术与工程', '第2章 细胞工程'),
        '胚胎工程': ('选择性必修三：生物技术与工程', '第3章 胚胎工程'),
        '发酵工程': ('选择性必修三：生物技术与工程', '第4章 发酵工程'),
        '生物技术的安全性与伦理问题': ('选择性必修三：生物技术与工程', '第5章 生物技术的安全性与伦理问题'),
    }
    
    for keyword, (tb, ch) in chapter_map.items():
        if keyword in filename:
            textbook = tb
            chapter = ch
            break
    
    exam_name = f"{textbook} {chapter} 专项训练"
    
    cursor.execute('INSERT OR IGNORE INTO exams (name, file_name, question_count) VALUES (?, ?, ?)',
                  (exam_name, filename, len(questions)))
    cursor.execute('SELECT id FROM exams WHERE name = ?', (exam_name,))
    exam_id = cursor.fetchone()[0]
    conn.commit()
    
    cursor.execute('SELECT MAX(number) FROM questions WHERE exam_id = ?', (exam_id,))
    max_num = cursor.fetchone()[0]
    start_num = max_num + 1 if max_num else 1
    
    inserted_count = 0
    for i, q in enumerate(questions):
        cursor.execute('''
            INSERT INTO questions (
                exam_id, number, stem, option_a, option_b, option_c, option_d, 
                answer, images, textbook, chapter, section, type, analysis
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            exam_id,
            start_num + i,
            q['stem'],
            q['options']['A'],
            q['options']['B'],
            q['options']['C'],
            q['options']['D'],
            q['answer'],
            json.dumps([]),
            textbook,
            chapter,
            section,
            q['type'],
            q['analysis']
        ))
        inserted_count += 1
    
    conn.commit()
    conn.close()
    
    print(f"从 {filename} 导入 {inserted_count} 道题")
    return inserted_count

def parse_all_files():
    biology_dir = 'D:/biology'
    total_inserted = 0
    
    for filename in os.listdir(biology_dir):
        if filename.endswith('.docx'):
            docx_path = os.path.join(biology_dir, filename)
            count = insert_questions_to_db(docx_path)
            total_inserted += count
    
    print(f"\n总共导入 {total_inserted} 道题")
    return total_inserted

if __name__ == '__main__':
    parse_all_files()