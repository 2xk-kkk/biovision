import re
import os
import json
import pdfplumber
from docx import Document


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


def extract_text_from_docx(docx_path):
    try:
        doc = Document(docx_path)
        paragraphs = []
        for para in doc.paragraphs:
            if para.text.strip():
                paragraphs.append(para.text)
        return ['\n'.join(paragraphs)]
    except Exception as e:
        print(f"Word解析错误: {e}")
        return []


def extract_text_from_file(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif ext == '.docx':
        return extract_text_from_docx(file_path)
    return []


def parse_questions(text):
    lines = text.split('\n')

    answer_section_start = -1
    for i, line in enumerate(lines):
        line_strip = line.strip()
        if re.match(r'^【\d+题答案】', line_strip):
            answer_section_start = i
            break
        if re.match(r'^答案[:：]', line_strip):
            answer_section_start = i
            break
        if re.match(r'^参考答案[:：]', line_strip):
            answer_section_start = i
            break
        if re.match(r'^选择题答案', line_strip):
            answer_section_start = i
            break
        if re.match(r'^非选择题答案', line_strip):
            answer_section_start = i
            break
        if re.match(r'^\d+\.答案[:：]', line_strip):
            answer_section_start = i
            break

    if answer_section_start > 0:
        lines = lines[:answer_section_start]

    questions = []
    current_question = None

    skip_keywords = ['答卷前', '答题前', '考生务必', '姓名', '准考证号', '答题卡', '考试结束', '填写在', '选择题：本题共', '非选择题：本题共']

    for line in lines:
        line = line.strip()
        if not line:
            continue

        q_match = re.match(r'^(\d+)[．.、)）]\s*(.+)$', line)
        if q_match:
            if current_question:
                if len(current_question.get('options', {})) >= 1 or current_question.get('stem', '').strip():
                    questions.append(current_question)

            q_num = int(q_match.group(1))
            q_stem = q_match.group(2)

            is_instruction = any(keyword in q_stem for keyword in skip_keywords)

            if is_instruction:
                current_question = None
                continue

            current_question = {
                'number': q_num,
                'stem': q_stem,
                'options': {}
            }

            has_options_in_line = bool(re.search(r'[ABCDabcd][．.、)）]\s*', q_stem))
            if has_options_in_line:
                parts = re.split(r'([ABCDabcd][．.、)）])', q_stem)
                stem_parts = []
                for i, part in enumerate(parts):
                    if re.match(r'[ABCDabcd][．.、)）]', part):
                        if i + 1 < len(parts):
                            opt_key = part[0].upper()
                            opt_value = parts[i + 1].strip()
                            if opt_key not in current_question['options']:
                                current_question['options'][opt_key] = opt_value
                    elif part.strip() and not re.match(r'^[ABCDabcd][．.、)）]$', part):
                        stem_parts.append(part)

                current_question['stem'] = ''.join(stem_parts).strip()
                if current_question['stem'].endswith('（') or current_question['stem'].endswith('('):
                    current_question['stem'] = current_question['stem'][:-1].strip()
            continue

        opt_line_match = re.findall(r'([ABCDabcd])[．.、)）]\s*([^\n]*?)(?=\s*[ABCDabcd][．.、)）]|$)', line)
        if opt_line_match and current_question:
            for key, value in opt_line_match:
                key_upper = key.upper()
                if key_upper not in current_question['options'] or not current_question['options'][key_upper]:
                    current_question['options'][key_upper] = value.strip()
            continue

        if current_question:
            if line.startswith(('A', 'B', 'C', 'D')):
                opt_key = line[0]
                opt_val = line[1:].lstrip('.．、').strip()
                if opt_key in 'ABCD':
                    current_question['options'][opt_key] = opt_val
            elif line.startswith('【') and ('题答案' in line or line.startswith('【答案】')):
                continue
            else:
                current_question['stem'] += ' ' + line

    if current_question:
        if len(current_question.get('options', {})) >= 1 or current_question.get('stem', '').strip():
            questions.append(current_question)

    return questions


def parse_answers(text):
    answers = {}

    lines = text.split('\n')
    current_num = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        num_match = re.match(r'【(\d+)题答案】', line)
        if num_match:
            current_num = int(num_match.group(1))
            continue

        ans_match = re.match(r'【答案】\s*(.+)$', line)
        if ans_match and current_num:
            ans_text = ans_match.group(1).strip()
            if re.match(r'^[ABCDabcd]+$', ans_text):
                ans_text = ans_text.upper()
            answers[current_num] = ans_text
            current_num = None
            continue

        ans_match2 = re.match(r'^(\d+)[．.、]\s*([ABCDabcd]+)', line)
        if ans_match2:
            answers[int(ans_match2.group(1))] = ans_match2.group(2).upper()
            continue

    return answers


def parse_document(file_path):
    ext = os.path.splitext(file_path)[1].lower()

    if ext == '.docx':
        try:
            from .extract_questions import parse_questions as parse_docx_questions
            exam_name = os.path.splitext(os.path.basename(file_path))[0]
            questions = parse_docx_questions(file_path, exam_name)

            answers = {q['number']: q['answer'] for q in questions if q.get('answer')}

            return exam_name, questions, answers
        except Exception as e:
            print(f"使用extract_questions解析失败: {e}")

    pages = extract_text_from_file(file_path)

    if not pages:
        return None, None, None

    full_text = '\n\n'.join(pages)

    title = os.path.splitext(os.path.basename(file_path))[0]

    questions = parse_questions(full_text)

    answers = parse_answers(full_text)

    for q in questions:
        if q['number'] in answers:
            q['answer'] = answers[q['number']]
        else:
            q['answer'] = ''

    return title, questions, answers


def save_questions(exam_id, questions):
    conn = None
    try:
        from database.db import get_db_connection
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('DELETE FROM questions WHERE exam_id = ?', (exam_id,))

        for q in questions:
            images_list = q.get('images', [])
            if isinstance(images_list, list):
                images_json = json.dumps(images_list)
            else:
                images_json = json.dumps([])

            cursor.execute('''
                INSERT INTO questions
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
                images_json
            ))

        conn.commit()
        return len(questions)
    except Exception as e:
        print(f"保存题目失败: {e}")
        if conn:
            conn.rollback()
        return 0
    finally:
        if conn:
            conn.close()


def parse_and_save(file_path, custom_title=None):
    try:
        title, questions, answers = parse_document(file_path)
        if custom_title:
            title = custom_title

        if not questions:
            return {'success': False, 'msg': f'文件 {os.path.basename(file_path)} 未能解析出题目，请检查文件格式', 'title': title}

        from database.db import get_db_connection
        conn = get_db_connection()
        conn.execute('PRAGMA busy_timeout = 5000')
        cursor = conn.cursor()

        cursor.execute('SELECT id FROM exams WHERE name = ?', (title,))
        exam_row = cursor.fetchone()

        if exam_row:
            exam_id = exam_row[0]
            cursor.execute('DELETE FROM questions WHERE exam_id = ?', (exam_id,))
            conn.commit()
            cursor.execute('UPDATE exams SET question_count = ? WHERE id = ?', (len(questions), exam_id))
        else:
            cursor.execute('INSERT INTO exams (name, question_count) VALUES (?, ?)', (title, len(questions)))
            conn.commit()
            cursor.execute('SELECT id FROM exams WHERE name = ?', (title,))
            exam_id = cursor.fetchone()[0]

        for q in questions:
            images_list = q.get('images', [])
            if isinstance(images_list, list):
                images_json = json.dumps(images_list)
            else:
                images_json = json.dumps([])

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
                images_json
            ))

        conn.commit()
        conn.close()

        answer_count = sum(1 for q in questions if q.get('answer'))

        return {
            'success': True,
            'msg': f'成功解析 {len(questions)} 道题，{answer_count} 个答案',
            'title': title,
            'question_count': len(questions),
            'answer_count': answer_count
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {'success': False, 'msg': f'解析保存失败: {str(e)}', 'title': custom_title or os.path.basename(file_path)}
