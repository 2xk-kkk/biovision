def add_exam(db, name, file_name, question_count=0):
    cursor = db.cursor()
    try:
        cursor.execute('INSERT OR IGNORE INTO exams (name, file_name, question_count) VALUES (?, ?, ?)',
                       (name, file_name, question_count))
        db.commit()
        cursor.execute('SELECT id FROM exams WHERE name = ?', (name,))
        return cursor.fetchone()[0]
    except Exception as e:
        db.rollback()
        raise e

def get_exam_id(db, name):
    cursor = db.cursor()
    cursor.execute('SELECT id FROM exams WHERE name = ?', (name,))
    result = cursor.fetchone()
    return result[0] if result else None

import json

def add_question(db, exam_id, number, stem, option_a, option_b, option_c, option_d, answer, images=None):
    cursor = db.cursor()
    try:
        images_json = json.dumps(images or [])
        cursor.execute('''
            INSERT OR REPLACE INTO questions 
            (exam_id, number, stem, option_a, option_b, option_c, option_d, answer, images)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (exam_id, number, stem, option_a, option_b, option_c, option_d, answer, images_json))
        db.commit()
        return cursor.lastrowid
    except Exception as e:
        db.rollback()
        raise e

def get_questions_by_exam(db, exam_id):
    cursor = db.cursor()
    cursor.execute('SELECT id, number, stem, option_a, option_b, option_c, option_d, answer, images, type, analysis FROM questions WHERE exam_id = ? ORDER BY number', (exam_id,))
    questions = []
    for row in cursor.fetchall():
        images = json.loads(row[8]) if row[8] else []
        questions.append({
            'id': row[0],
            'number': row[1],
            'stem': row[2],
            'options': {
                'A': row[3],
                'B': row[4],
                'C': row[5],
                'D': row[6]
            },
            'answer': row[7],
            'images': images,
            'type': row[9] if row[9] else '',
            'analysis': row[10] if row[10] else ''
        })
    return questions

def get_exams(db):
    cursor = db.cursor()
    cursor.execute('SELECT id, name, file_name, question_count, create_at FROM exams ORDER BY create_at DESC')
    exams = []
    for row in cursor.fetchall():
        exams.append({
            'id': row[0],
            'name': row[1],
            'file_name': row[2],
            'question_count': row[3],
            'create_at': row[4]
        })
    return exams

def save_user_answer(db, user_id, question_id, answer, is_correct):
    cursor = db.cursor()
    try:
        cursor.execute('''
            INSERT INTO user_answers (user_id, question_id, answer, is_correct, wrong_count, mastered)
            VALUES (?, ?, ?, ?, CASE WHEN ? = 0 THEN 1 ELSE 0 END, 0)
            ON CONFLICT(user_id, question_id) DO UPDATE SET
                answer = excluded.answer,
                is_correct = excluded.is_correct,
                wrong_count = CASE WHEN excluded.is_correct = 0 THEN user_answers.wrong_count + 1 ELSE user_answers.wrong_count END,
                mastered = CASE WHEN excluded.is_correct = 1 THEN 1 ELSE user_answers.mastered END,
                create_at = CURRENT_TIMESTAMP
        ''', (user_id, question_id, answer, is_correct, is_correct))
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise e

def get_wrong_answers(db, user_id, textbook=None, status=None, page=1, page_size=20):
    cursor = db.cursor()
    offset = (page - 1) * page_size
    
    query = '''
        SELECT q.id, q.stem, q.option_a, q.option_b, q.option_c, q.option_d, q.answer, q.textbook,
               ua.wrong_count, ua.mastered, ua.answer as user_answer, ua.create_at as last_answer_time
        FROM user_answers ua
        JOIN questions q ON ua.question_id = q.id
        WHERE ua.user_id = ? AND ua.is_correct = 0
    '''
    params = [user_id]
    
    if textbook and textbook != '全部':
        query += ' AND q.textbook = ?'
        params.append(textbook)
    
    if status == 'unmastered':
        query += ' AND ua.mastered = 0'
    elif status == 'mastered':
        query += ' AND ua.mastered = 1'
    
    query += ' ORDER BY ua.create_at DESC LIMIT ? OFFSET ?'
    params.extend([page_size, offset])
    
    cursor.execute(query, params)
    items = []
    for row in cursor.fetchall():
        items.append({
            'question_id': row[0],
            'stem': row[1],
            'option_a': row[2],
            'option_b': row[3],
            'option_c': row[4],
            'option_d': row[5],
            'correct_answer': row[6],
            'textbook': row[7],
            'wrong_count': row[8] or 0,
            'mastered': row[9] or 0,
            'user_answer': row[10],
            'last_answer_time': row[11]
        })
    
    count_query = '''
        SELECT COUNT(*) FROM user_answers ua
        JOIN questions q ON ua.question_id = q.id
        WHERE ua.user_id = ? AND ua.is_correct = 0
    '''
    count_params = [user_id]
    if textbook and textbook != '全部':
        count_query += ' AND q.textbook = ?'
        count_params.append(textbook)
    if status == 'unmastered':
        count_query += ' AND ua.mastered = 0'
    elif status == 'mastered':
        count_query += ' AND ua.mastered = 1'
    
    cursor.execute(count_query, count_params)
    total = cursor.fetchone()[0]
    total_pages = (total + page_size - 1) // page_size
    
    return {
        'items': items,
        'total': total,
        'page': page,
        'total_pages': total_pages,
        'page_size': page_size
    }

def get_wrong_answer_stats(db, user_id):
    cursor = db.cursor()
    
    cursor.execute('''
        SELECT COUNT(*) FROM user_answers ua
        JOIN questions q ON ua.question_id = q.id
        WHERE ua.user_id = ? AND ua.is_correct = 0
    ''', (user_id,))
    total = cursor.fetchone()[0]
    
    cursor.execute('''
        SELECT COUNT(*) FROM user_answers ua
        JOIN questions q ON ua.question_id = q.id
        WHERE ua.user_id = ? AND ua.is_correct = 0 AND ua.mastered = 1
    ''', (user_id,))
    mastered = cursor.fetchone()[0]
    
    unmastered = total - mastered
    mastery_rate = int((mastered / total) * 100) if total > 0 else 0
    
    return {
        'total': total,
        'mastered': mastered,
        'unmastered': unmastered,
        'mastery_rate': mastery_rate
    }

def mark_mastered(db, user_id, question_id, mastered=1):
    cursor = db.cursor()
    try:
        cursor.execute('''
            UPDATE user_answers SET mastered = ? WHERE user_id = ? AND question_id = ?
        ''', (mastered, user_id, question_id))
        db.commit()
        return cursor.rowcount > 0
    except Exception as e:
        db.rollback()
        raise e

def retry_wrong_answer(db, user_id, question_id, answer, is_correct):
    cursor = db.cursor()
    try:
        cursor.execute('''
            UPDATE user_answers SET 
                answer = ?, 
                is_correct = ?,
                wrong_count = CASE WHEN ? = 0 THEN wrong_count + 1 ELSE wrong_count END,
                mastered = CASE WHEN ? = 1 THEN 1 ELSE mastered END,
                create_at = CURRENT_TIMESTAMP
            WHERE user_id = ? AND question_id = ?
        ''', (answer, is_correct, is_correct, is_correct, user_id, question_id))
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise e

def get_user_answers(db, user_id, exam_id=None):
    cursor = db.cursor()
    if exam_id:
        cursor.execute('''
            SELECT ua.question_id, ua.answer, ua.is_correct, q.number
            FROM user_answers ua
            JOIN questions q ON ua.question_id = q.id
            WHERE ua.user_id = ? AND q.exam_id = ?
            ORDER BY q.number
        ''', (user_id, exam_id))
    else:
        cursor.execute('''
            SELECT ua.question_id, ua.answer, ua.is_correct, q.number, q.exam_id
            FROM user_answers ua
            JOIN questions q ON ua.question_id = q.id
            WHERE ua.user_id = ?
            ORDER BY q.exam_id, q.number
        ''', (user_id,))
    answers = {}
    for row in cursor.fetchall():
        if exam_id:
            answers[row[3]] = {'answer': row[1], 'is_correct': row[2]}
        else:
            exam_key = row[4]
            if exam_key not in answers:
                answers[exam_key] = {}
            answers[exam_key][row[3]] = {'answer': row[1], 'is_correct': row[2]}
    return answers

def get_exam_stats(db, exam_id, user_id):
    cursor = db.cursor()
    cursor.execute('SELECT COUNT(*) FROM questions WHERE exam_id = ?', (exam_id,))
    total = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM user_answers ua JOIN questions q ON ua.question_id = q.id WHERE q.exam_id = ? AND ua.user_id = ?', (exam_id, user_id))
    answered = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(*) FROM user_answers ua JOIN questions q ON ua.question_id = q.id WHERE q.exam_id = ? AND ua.user_id = ? AND ua.is_correct = 1', (exam_id, user_id))
    correct = cursor.fetchone()[0]
    
    return {
        'total': total,
        'answered': answered,
        'correct': correct,
        'wrong': answered - correct
    }

def get_questions_by_textbook(db, textbook=None, chapter=None, section=None, question_type=None):
    cursor = db.cursor()
    
    query = 'SELECT id, number, stem, option_a, option_b, option_c, option_d, answer, images, textbook, chapter, section, type, analysis FROM questions WHERE 1=1'
    params = []
    
    if textbook:
        query += ' AND textbook = ?'
        params.append(textbook)
    
    if chapter:
        query += ' AND chapter = ?'
        params.append(chapter)
    
    if section:
        query += ' AND section = ?'
        params.append(section)
    
    if question_type and question_type != 'all':
        query += ' AND type = ?'
        params.append(question_type)
    
    query += ' ORDER BY number'
    
    cursor.execute(query, params)
    questions = []
    for row in cursor.fetchall():
        images_str = row[8] if row[8] else ''
        try:
            images = json.loads(images_str) if images_str else []
        except:
            images = []
        questions.append({
            'id': row[0],
            'number': row[1],
            'stem': row[2],
            'options': {
                'A': row[3],
                'B': row[4],
                'C': row[5],
                'D': row[6]
            },
            'answer': row[7],
            'images': images,
            'textbook': row[9],
            'chapter': row[10],
            'section': row[11],
            'type': row[12] if row[12] else '',
            'analysis': row[13] if row[13] else ''
        })
    return questions

def get_questions_by_type(db, textbook=None, chapter=None, section=None, question_type=None):
    cursor = db.cursor()
    
    query = 'SELECT id, number, stem, option_a, option_b, option_c, option_d, answer, images, textbook, chapter, section, type, analysis FROM questions WHERE 1=1'
    params = []
    
    if textbook:
        query += ' AND textbook = ?'
        params.append(textbook)
    
    if chapter:
        query += ' AND chapter = ?'
        params.append(chapter)
    
    if section:
        query += ' AND section = ?'
        params.append(section)
    
    if question_type:
        query += ' AND type = ?'
        params.append(question_type)
    
    cursor.execute(query, params)
    questions = []
    for row in cursor.fetchall():
        images_str = row[8] if row[8] else ''
        try:
            images = json.loads(images_str) if images_str else []
        except:
            images = []
        questions.append({
            'id': row[0],
            'number': row[1],
            'stem': row[2],
            'options': {
                'A': row[3],
                'B': row[4],
                'C': row[5],
                'D': row[6]
            },
            'answer': row[7],
            'images': images,
            'textbook': row[9],
            'chapter': row[10],
            'section': row[11],
            'type': row[12] if row[12] else '',
            'analysis': row[13] if row[13] else ''
        })
    return questions