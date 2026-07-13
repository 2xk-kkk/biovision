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
    cursor.execute('SELECT id, number, stem, option_a, option_b, option_c, option_d, answer, images FROM questions WHERE exam_id = ? ORDER BY number', (exam_id,))
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
            'images': images
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
            INSERT OR REPLACE INTO user_answers 
            (user_id, question_id, answer, is_correct)
            VALUES (?, ?, ?, ?)
        ''', (user_id, question_id, answer, is_correct))
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
<<<<<<< HEAD
    }

def get_random_choice_questions(db, count=10):
    cursor = db.cursor()
    cursor.execute('''
        SELECT id, number, stem, option_a, option_b, option_c, option_d, answer, images, exam_id
        FROM questions 
        WHERE option_a IS NOT NULL AND option_a != ''
        ORDER BY RANDOM() 
        LIMIT ?
    ''', (count,))
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
            'exam_id': row[9]
        })
    return questions
=======
    }
>>>>>>> 3dda3ed5df70478afd4f8e6ec969e6318ce519a0
