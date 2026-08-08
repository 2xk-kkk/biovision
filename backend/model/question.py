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

def normalize_textbook_name(textbook):
    # 完整名称映射（精确匹配优先）
    full_map = {
        '必修一：分子与细胞': '必修一：分子与细胞',
        '必修二：遗传与进化': '必修二：遗传与进化',
        '选择性必修一：稳态与调节': '选择性必修一：稳态与调节',
        '选择性必修二：生物与环境': '选择性必修二：生物与环境',
        '选择性必修三：生物技术与工程': '选择性必修三：生物技术与工程',
        '选修一：稳态与调节': '选择性必修一：稳态与调节',
        '选修二：生物与环境': '选择性必修二：生物与环境',
        '选修三：生物技术与工程': '选择性必修三：生物技术与工程',
    }
    if textbook in full_map:
        return full_map[textbook]
    # 简称匹配（仅当不包含"选择性"时，防止"选择性必修一"被"必修一"误匹配）
    short_map = {
        '必修一': '必修一：分子与细胞',
        '必修二': '必修二：遗传与进化',
        '选修一': '选择性必修一：稳态与调节',
        '选修二': '选择性必修二：生物与环境',
        '选修三': '选择性必修三：生物技术与工程',
    }
    for short, full in short_map.items():
        if short in textbook and '选择性' not in textbook:
            return full
    return textbook

def get_questions_by_textbook(db, textbook=None, chapter=None, section=None, question_type=None):
    cursor = db.cursor()
    
    if textbook:
        textbook = normalize_textbook_name(textbook)
    
    query = 'SELECT id, number, stem, option_a, option_b, option_c, option_d, answer, images, textbook, chapter, section, type, analysis FROM questions WHERE 1=1'
    params = []
    
    if textbook:
        short_name = textbook.split('：')[-1] if '：' in textbook else textbook
        query += ' AND (textbook = ? OR textbook LIKE ?)'
        params.append(textbook)
        params.append(f'%{short_name}%')

    if chapter:
        query += ' AND chapter LIKE ?'
        params.append(f'{chapter}%')

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

def get_daily_answer_counts(db, user_id, days=90):
    """获取用户最近N天每天的做题数量，返回 {date_str: count} 字典（使用本地时间）"""
    cursor = db.cursor()
    cursor.execute('''
        SELECT DATE(create_at, 'localtime') as answer_date, COUNT(*) as count
        FROM user_answers
        WHERE user_id = ?
        AND create_at >= DATETIME('now', 'localtime', ?)
        GROUP BY DATE(create_at, 'localtime')
        ORDER BY answer_date
    ''', (user_id, f'-{days} days'))
    results = {}
    for row in cursor.fetchall():
        results[row[0]] = row[1]
    return results


def get_total_answer_count(db, user_id):
    """获取用户题库总做题数（只统计教材题目，不包含真题试卷）"""
    cursor = db.cursor()
    cursor.execute('''
        SELECT COUNT(*) FROM user_answers ua
        JOIN questions q ON ua.question_id = q.id
        WHERE ua.user_id = ? AND q.textbook IS NOT NULL AND q.textbook != ''
    ''', (user_id,))
    row = cursor.fetchone()
    return row[0] if row else 0


def get_textbook_chapter_progress(db, textbook, user_id):
    """获取某本教材的章节做题进度。
    返回 [{title, sections: [{title, total, answered, correct, accuracy}], total, answered, correct, accuracy}]"""
    textbook = normalize_textbook_name(textbook)
    cursor = db.cursor()

    # 获取该教材所有章节和节
    cursor.execute('''
        SELECT chapter, section, COUNT(*)
        FROM questions
        WHERE textbook IS NOT NULL AND textbook != ''
        AND (textbook = ? OR textbook LIKE ?)
        GROUP BY chapter, section
        ORDER BY chapter, section
    ''', (textbook, f'%{textbook.split("：")[-1] if "：" in textbook else textbook}%'))

    # Build structure from raw data
    chapters_map = {}
    for row in cursor.fetchall():
        ch, sec, cnt = row
        ch = ch if ch else '综合'
        sec = sec if sec else '综合'
        if ch not in chapters_map:
            chapters_map[ch] = {'sections': {}, 'total': 0}
        chapters_map[ch]['sections'][sec] = {'total': cnt, 'answered': 0, 'correct': 0}
        chapters_map[ch]['total'] += cnt

    # 获取用户已做题数
    cursor.execute('''
        SELECT q.chapter, q.section, COUNT(*), SUM(ua.is_correct)
        FROM user_answers ua
        JOIN questions q ON ua.question_id = q.id
        WHERE ua.user_id = ? AND (q.textbook = ? OR q.textbook LIKE ?)
        GROUP BY q.chapter, q.section
    ''', (user_id, textbook, f'%{textbook.split("：")[-1] if "：" in textbook else textbook}%'))

    for row in cursor.fetchall():
        ch, sec, answered, correct = row
        ch = ch if ch else '综合'
        sec = sec if sec else '综合'
        if ch in chapters_map and sec in chapters_map[ch]['sections']:
            chapters_map[ch]['sections'][sec]['answered'] = answered or 0
            chapters_map[ch]['sections'][sec]['correct'] = correct or 0

    # Convert to ordered list
    result = []
    for ch_title in chapters_map:
        ch_data = chapters_map[ch_title]
        sections = []
        ch_answered = 0
        ch_correct = 0
        for sec_title, sec_data in ch_data['sections'].items():
            acc = round((sec_data['correct'] / sec_data['total']) * 100) if sec_data['total'] > 0 else 0
            sections.append({
                'title': sec_title,
                'total': sec_data['total'],
                'answered': sec_data['answered'],
                'correct': sec_data['correct'],
                'accuracy': acc
            })
            ch_answered += sec_data['answered']
            ch_correct += sec_data['correct']

        ch_total = ch_data['total']
        ch_acc = round((ch_correct / ch_total) * 100) if ch_total > 0 else 0
        result.append({
            'title': ch_title,
            'sections': sections,
            'total': ch_total,
            'answered': ch_answered,
            'correct': ch_correct,
            'accuracy': ch_acc
        })

    return result


def get_textbook_progress(db, user_id):
    """获取用户每本教材的做题进度，返回列表 [{name, total, answered, correct, rate}]"""
    # 先拿所有教材题目数
    cursor = db.cursor()
    cursor.execute('''
        SELECT textbook, COUNT(*) FROM questions
        WHERE textbook IS NOT NULL AND textbook != ''
        GROUP BY textbook
    ''')
    raw_counts = {}
    for row in cursor.fetchall():
        name = normalize_textbook_name(row[0])
        raw_counts[name] = raw_counts.get(name, 0) + row[1]

    # 拿用户已做题数
    cursor.execute('''
        SELECT q.textbook, COUNT(*)
        FROM user_answers ua
        JOIN questions q ON ua.question_id = q.id
        WHERE ua.user_id = ? AND q.textbook IS NOT NULL AND q.textbook != ''
        GROUP BY q.textbook
    ''', (user_id,))
    raw_answered = {}
    for row in cursor.fetchall():
        name = normalize_textbook_name(row[0])
        raw_answered[name] = raw_answered.get(name, 0) + row[1]

    # 拿用户做对的题数
    cursor.execute('''
        SELECT q.textbook, COUNT(*)
        FROM user_answers ua
        JOIN questions q ON ua.question_id = q.id
        WHERE ua.user_id = ? AND ua.is_correct = 1 AND q.textbook IS NOT NULL AND q.textbook != ''
        GROUP BY q.textbook
    ''', (user_id,))
    raw_correct = {}
    for row in cursor.fetchall():
        name = normalize_textbook_name(row[0])
        raw_correct[name] = raw_correct.get(name, 0) + row[1]

    # 按固定顺序排列
    textbook_order = [
        '必修一：分子与细胞',
        '必修二：遗传与进化',
        '选择性必修一：稳态与调节',
        '选择性必修二：生物与环境',
        '选择性必修三：生物技术与工程',
    ]

    result = []
    for name in textbook_order:
        total = raw_counts.get(name, 0)
        answered = raw_answered.get(name, 0)
        correct = raw_correct.get(name, 0)
        rate = round((answered / total) * 100) if total > 0 else 0
        result.append({
            'name': name,
            'total': total,
            'answered': answered,
            'correct': correct,
            'rate': rate
        })

    return result


def get_question_bank_structure(db):
    """获取题库结构：教材→章→节，含每题数量"""
    cursor = db.cursor()
    cursor.execute('''
        SELECT textbook, chapter, section, COUNT(*) as cnt
        FROM questions
        WHERE textbook IS NOT NULL AND textbook != ''
        GROUP BY textbook, chapter, section
        ORDER BY textbook, chapter, section
    ''')
    structure = {}
    for row in cursor.fetchall():
        textbook, chapter, section, cnt = row
        if textbook not in structure:
            structure[textbook] = {}
        if chapter not in structure[textbook]:
            structure[textbook][chapter] = {}
        structure[textbook][chapter][section if section else '综合'] = cnt

    # 转为列表格式
    result = []
    for textbook, chapters in structure.items():
        textbook_data = {
            "name": textbook,
            "chapters": [],
            "question_count": 0
        }
        for chapter, sections in chapters.items():
            chapter_data = {
                "name": chapter if chapter else "综合",
                "sections": [],
                "question_count": 0
            }
            for section, cnt in sections.items():
                chapter_data["sections"].append({
                    "name": section,
                    "question_count": cnt
                })
                chapter_data["question_count"] += cnt
            textbook_data["chapters"].append(chapter_data)
            textbook_data["question_count"] += chapter_data["question_count"]
        result.append(textbook_data)

    return result


def get_questions_by_type(db, textbook=None, chapter=None, section=None, question_type=None):
    cursor = db.cursor()
    
    query = 'SELECT id, number, stem, option_a, option_b, option_c, option_d, answer, images, textbook, chapter, section, type, analysis FROM questions WHERE 1=1'
    params = []
    
    if textbook:
        textbook = normalize_textbook_name(textbook)
        query += ' AND textbook = ?'
        params.append(textbook)
    
    if chapter:
        query += ' AND chapter LIKE ?'
        params.append(f'{chapter}%')
    
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


def add_to_wrong_book(db, user_id, question_id, user_answer=None):
    """将题目加入错题本"""
    cursor = db.cursor()
    try:
        cursor.execute('''
            INSERT INTO user_answers (user_id, question_id, answer, is_correct, wrong_count, mastered)
            VALUES (?, ?, ?, 0, 1, 0)
            ON CONFLICT(user_id, question_id) DO UPDATE SET
                answer = CASE WHEN excluded.answer IS NOT NULL AND excluded.answer != '' THEN excluded.answer ELSE user_answers.answer END,
                is_correct = 0,
                wrong_count = user_answers.wrong_count + 1,
                mastered = 0,
                create_at = CURRENT_TIMESTAMP
        ''', (user_id, question_id, user_answer))
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise e


def get_related_questions_by_knowledge(db, user_id, question_id, limit=5):
    """根据题目的知识点标签推荐相关题目。

    优先按 knowledge_tags 重合度排序，无标签时回退到章节/教材匹配。
    """
    import json
    cursor = db.cursor()

    # 获取当前题目的章节信息和知识点标签
    cursor.execute('''
        SELECT textbook, chapter, section, knowledge_tags FROM questions WHERE id = ?
    ''', (question_id,))
    current_question = cursor.fetchone()

    if not current_question:
        return []

    textbook, chapter, section, knowledge_tags_json = current_question

    # 解析知识点标签
    source_tags = []
    try:
        if knowledge_tags_json and knowledge_tags_json != '[]':
            source_tags = json.loads(knowledge_tags_json)  # [[kp_id, score], ...]
    except (json.JSONDecodeError, TypeError):
        source_tags = []

    if source_tags:
        # ===== 路径 A：知识点标签匹配 =====
        source_kp_ids = {t[0]: t[1] for t in source_tags}

        # 查询候选题目：同章 + 同教材（扩大池子做标签重合）
        query = '''
            SELECT q.id, q.stem, q.option_a, q.option_b, q.option_c, q.option_d,
                   q.answer, q.textbook, q.chapter, q.section, q.type, q.analysis,
                   q.knowledge_tags,
                   COALESCE(ua.wrong_count, 0) as wrong_count,
                   COALESCE(ua.mastered, 0) as mastered,
                   ua.answer as user_answer
            FROM questions q
            LEFT JOIN user_answers ua ON q.id = ua.question_id AND ua.user_id = ?
            WHERE q.id != ?
            AND (ua.is_correct = 0 OR ua.is_correct IS NULL)
        '''
        params = [user_id, question_id]

        # 先用章节条件缩小候选池
        conditions = []
        if chapter:
            conditions.append('q.chapter = ?')
            params.append(chapter)
        if textbook:
            conditions.append('q.textbook = ?')
            params.append(textbook)
        if section and chapter:
            conditions.append('(q.section = ? AND q.chapter = ?)')
            params.extend([section, chapter])

        if conditions:
            query += ' AND (' + ' OR '.join(conditions) + ')'

        cursor.execute(query, params)
        candidates = cursor.fetchall()

        # 对每道候选计算标签重合分数
        scored = []
        for row in candidates:
            candidate_tags_json = row[12]  # knowledge_tags column
            candidate_tags = []
            try:
                if candidate_tags_json and candidate_tags_json != '[]':
                    candidate_tags = json.loads(candidate_tags_json)
            except (json.JSONDecodeError, TypeError):
                pass

            # 计算重合分数
            overlap_score = 0.0
            shared_kp_ids = []
            for ckp_id, c_score in candidate_tags:
                if ckp_id in source_kp_ids:
                    overlap_score += min(source_kp_ids[ckp_id], c_score)
                    shared_kp_ids.append(ckp_id)

            # 章节/教材加分
            bonus = 0.0
            c_textbook = row[7] or ''
            c_chapter = row[8] or ''
            c_section = row[9] or ''

            if section and c_section == section and chapter and c_chapter == chapter:
                bonus += 3.0
            elif chapter and c_chapter == chapter:
                bonus += 2.0
            elif textbook and c_textbook == textbook:
                bonus += 1.0

            # 综合分 = 标签重合 × 10 + 章节加分 + 之前错过加分
            score = overlap_score * 10 + bonus
            if row[13] and row[13] > 0:  # wrong_count
                score += 1.0
            if row[14] is None or row[14] == 0:  # 未做过
                score += 0.5

            scored.append((score, row, shared_kp_ids))

        # 按分数降序排序
        scored.sort(key=lambda x: x[0], reverse=True)

        # 取 top-N，去重（按 ID）
        seen_ids = set()
        items = []
        for score, row, shared_kp_ids in scored:
            qid = row[0]
            if qid in seen_ids:
                continue
            seen_ids.add(qid)

            item = {
                'id': row[0],
                'stem': row[1],
                'options': {
                    'A': row[2],
                    'B': row[3],
                    'C': row[4],
                    'D': row[5]
                },
                'answer': row[6],
                'textbook': row[7] or '',
                'chapter': row[8] or '',
                'section': row[9] or '',
                'type': row[10] or '',
                'analysis': row[11] or '',
                'wrong_count': row[13] or 0,
                'mastered': row[14] or 0,
                'user_answer': row[15] or '',
                '_shared_kp_ids': shared_kp_ids,
            }
            items.append(item)

            if len(items) >= limit:
                break

        return items

    else:
        # ===== 路径 B：无知识点标签，回退到章节/教材匹配 =====
        query = '''
            SELECT q.id, q.stem, q.option_a, q.option_b, q.option_c, q.option_d,
                   q.answer, q.textbook, q.chapter, q.section, q.type, q.analysis,
                   COALESCE(ua.wrong_count, 0) as wrong_count,
                   COALESCE(ua.mastered, 0) as mastered,
                   ua.answer as user_answer
            FROM questions q
            LEFT JOIN user_answers ua ON q.id = ua.question_id AND ua.user_id = ?
            WHERE q.id != ?
        '''
        params = [user_id, question_id]

        conditions = []
        if section and chapter:
            conditions.append('(q.section = ? AND q.chapter = ?)')
            params.extend([section, chapter])
        if chapter:
            conditions.append('(q.chapter = ?)')
            params.append(chapter)
        if textbook:
            conditions.append('(q.textbook = ?)')
            params.append(textbook)

        if conditions:
            query += ' AND (' + ' OR '.join(conditions) + ')'

        query += ' AND (ua.is_correct = 0 OR ua.is_correct IS NULL)'

        query += ' ORDER BY '
        order_clauses = []
        if section and chapter:
            order_clauses.append('CASE WHEN q.section = ? AND q.chapter = ? THEN 0 ELSE 1 END')
            params.extend([section, chapter])
        if chapter:
            order_clauses.append('CASE WHEN q.chapter = ? THEN 0 ELSE 1 END')
            params.append(chapter)
        order_clauses.append('CASE WHEN ua.question_id IS NULL THEN 0 ELSE 1 END')
        order_clauses.append('COALESCE(ua.wrong_count, 0) DESC')

        query += ', '.join(order_clauses) + ' LIMIT ?'
        params.append(limit)

        cursor.execute(query, params)

        items = []
        for row in cursor.fetchall():
            items.append({
                'id': row[0],
                'stem': row[1],
                'options': {
                    'A': row[2],
                    'B': row[3],
                    'C': row[4],
                    'D': row[5]
                },
                'answer': row[6],
                'textbook': row[7] or '',
                'chapter': row[8] or '',
                'section': row[9] or '',
                'type': row[10] or '',
                'analysis': row[11] or '',
                'wrong_count': row[12] or 0,
                'mastered': row[13] or 0,
                'user_answer': row[14] or ''
            })

        return items


def get_question_by_id(db, question_id):
    """根据ID获取单个题目"""
    cursor = db.cursor()
    cursor.execute('''
        SELECT id, stem, option_a, option_b, option_c, option_d, answer, 
               textbook, chapter, section, type, analysis, images
        FROM questions WHERE id = ?
    ''', (question_id,))
    row = cursor.fetchone()
    
    if not row:
        return None
    
    images_str = row[12] if row[12] else ''
    try:
        images = json.loads(images_str) if images_str else []
    except:
        images = []
    
    return {
        'id': row[0],
        'stem': row[1],
        'options': {
            'A': row[2],
            'B': row[3],
            'C': row[4],
            'D': row[5]
        },
        'answer': row[6],
        'textbook': row[7] or '',
        'chapter': row[8] or '',
        'section': row[9] or '',
        'type': row[10] or '',
        'analysis': row[11] or '',
        'images': images
    }