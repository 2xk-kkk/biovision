import re
import pdfplumber
from database.db import get_db_connection, add_column_if_not_exists


def extract_text_from_pdf(pdf_path):
    try:
        with pdfplumber.open(pdf_path) as pdf:
            pages = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    pages.append(text)
            return pages
    except Exception as e:
        print(f"PDF解析错误: {e}")
        return []


def parse_questions_from_text(pages):
    questions = []
    current_question = None
    current_options = []
    
    full_text = '\n\n'.join(pages)
    
    lines = full_text.split('\n')
    line_index = 0
    
    while line_index < len(lines):
        line = lines[line_index].strip()
        if not line:
            line_index += 1
            continue
        
        question_match = re.match(r'^(\d+)\.\s*(.+)$', line)
        if question_match:
            if current_question:
                current_question['options'] = current_options
                questions.append(current_question)
            
            question_number = int(question_match.group(1))
            question_stem = question_match.group(2)
            
            line_index += 1
            while line_index < len(lines):
                next_line = lines[line_index].strip()
                option_pattern = re.match(r'^([ABCD])[．.、]\s*(.+)$', next_line)
                if option_pattern or next_line.startswith('(') or re.match(r'^\d+\.', next_line):
                    break
                question_stem += ' ' + next_line
                line_index += 1
            
            current_question = {
                'number': question_number,
                'stem': question_stem,
                'options': {}
            }
            current_options = {}
            continue
        
        option_match = re.match(r'^([ABCD])[．.、]\s*(.+)$', line)
        if option_match and current_question:
            option_key = option_match.group(1)
            option_text = option_match.group(2)
            
            line_index += 1
            while line_index < len(lines):
                next_line = lines[line_index].strip()
                next_option_match = re.match(r'^([ABCD])[．.、]\s*(.+)$', next_line)
                if next_option_match or re.match(r'^\d+\.', next_line):
                    break
                option_text += ' ' + next_line
                line_index += 1
            
            current_options[option_key] = option_text
            continue
        
        line_index += 1
    
    if current_question:
        current_question['options'] = current_options
        questions.append(current_question)
    
    return questions


def parse_answers_from_last_page(pages):
    if not pages:
        return {}
    
    last_page = pages[-1]
    
    answers = {}
    
    patterns = [
        r'[答案参考答案]\s*[:：]\s*([A-Da-d]+)',
        r'(\d+)\s*[．.、]\s*([ABCDabcd])',
        r'^([ABCDabcd])\s*$',
        r'(\d+)\s*\.\s*([ABCDabcd])'
    ]
    
    lines = last_page.split('\n')
    current_num = 1
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        num_answer_match = re.match(r'^(\d+)\s*[．.、]\s*([ABCDabcd])$', line)
        if num_answer_match:
            num = int(num_answer_match.group(1))
            answer = num_answer_match.group(2).upper()
            answers[num] = answer
            current_num = num + 1
            continue
        
        num_answer_match2 = re.match(r'^(\d+)\s*\.\s*([ABCDabcd])$', line)
        if num_answer_match2:
            num = int(num_answer_match2.group(1))
            answer = num_answer_match2.group(2).upper()
            answers[num] = answer
            current_num = num + 1
            continue
        
        pure_answer_match = re.match(r'^[ABCDabcd]+$', line)
        if pure_answer_match:
            answer_str = pure_answer_match.group(0).upper()
            for char in answer_str:
                if char in 'ABCD':
                    answers[current_num] = char
                    current_num += 1
            continue
        
        answer_section_match = re.search(r'[答案参考答案]\s*[:：]\s*([A-Da-d]+)', line)
        if answer_section_match:
            answer_str = answer_section_match.group(1).upper()
            for char in answer_str:
                if char in 'ABCD':
                    answers[current_num] = char
                    current_num += 1
            continue
    
    return answers


def parse_pdf(pdf_path):
    pages = extract_text_from_pdf(pdf_path)
    
    if not pages:
        return None, None
    
    questions = parse_questions_from_text(pages)
    answers = parse_answers_from_last_page(pages)
    
    for q in questions:
        if q['number'] in answers:
            q['answer'] = answers[q['number']]
        else:
            q['answer'] = ''
    
    return questions, answers


def save_questions_to_db(exam_id, questions):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    for q in questions:
        options_str = json.dumps(q['options'], ensure_ascii=False) if q['options'] else ''
        cursor.execute('''
            INSERT OR REPLACE INTO questions 
            (exam_id, number, stem, option_a, option_b, option_c, option_d, answer, images)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            exam_id,
            q['number'],
            q['stem'],
            q['options'].get('A', ''),
            q['options'].get('B', ''),
            q['options'].get('C', ''),
            q['options'].get('D', ''),
            q.get('answer', ''),
            ''
        ))
    
    conn.commit()
    conn.close()
    
    return len(questions)


import json

def parse_and_save_pdf(exam_id, pdf_path):
    questions, answers = parse_pdf(pdf_path)
    
    if not questions:
        return {'success': False, 'msg': '未能解析出题目'}
    
    saved_count = save_questions_to_db(exam_id, questions)
    
    return {
        'success': True,
        'msg': f'成功解析 {len(questions)} 道题，保存 {saved_count} 道题',
        'question_count': len(questions),
        'answer_count': len(answers)
    }