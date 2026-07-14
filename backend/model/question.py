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
        # 使用 upsert 保留 wrong_count，每次答错时递增
        cursor.execute('''
            INSERT INTO user_answers (user_id, question_id, answer, is_correct, wrong_count, mastered)
            VALUES (?, ?, ?, ?, CASE WHEN ? = 0 THEN 1 ELSE 0 END, 0)
            ON CONFLICT(user_id, question_id) DO UPDATE SET
                answer = excluded.answer,
                is_correct = excluded.is_correct,
                wrong_count = user_answers.wrong_count + CASE WHEN excluded.is_correct = 0 THEN 1 ELSE 0 END,
                create_at = CURRENT_TIMESTAMP
        ''', (user_id, question_id, answer, is_correct, is_correct))
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

# ========== 错题集相关函数 ==========

def get_wrong_answers(db, user_id, textbook=None, status=None, page=1, page_size=20):
    """获取用户的错题列表（wrong_count > 0）"""
    cursor = db.cursor()

    conditions = ['ua.user_id = ?', 'ua.wrong_count > 0']
    params = [user_id]

    if textbook and textbook != '全部':
        conditions.append('q.textbook = ?')
        params.append(textbook)

    if status == 'mastered':
        conditions.append('ua.mastered = 1')
    elif status == 'unmastered':
        conditions.append('ua.mastered = 0')
    # status == 'all' 或 None 不过滤

    where_clause = ' AND '.join(conditions)

    # 总数
    cursor.execute(f'''
        SELECT COUNT(*)
        FROM user_answers ua
        JOIN questions q ON ua.question_id = q.id
        WHERE {where_clause}
    ''', params)
    total = cursor.fetchone()[0]

    # 分页数据
    offset = (page - 1) * page_size
    cursor.execute(f'''
        SELECT
            ua.question_id,
            ua.answer AS user_answer,
            ua.is_correct,
            ua.wrong_count,
            ua.mastered,
            ua.create_at AS last_answer_time,
            q.number,
            q.stem,
            q.option_a,
            q.option_b,
            q.option_c,
            q.option_d,
            q.answer AS correct_answer,
            q.textbook,
            q.exam_id,
            q.images
        FROM user_answers ua
        JOIN questions q ON ua.question_id = q.id
        WHERE {where_clause}
        ORDER BY ua.mastered ASC, ua.wrong_count DESC, ua.create_at DESC
        LIMIT ? OFFSET ?
    ''', params + [page_size, offset])

    items = []
    for row in cursor.fetchall():
        items.append({
            'question_id': row[0],
            'user_answer': row[1],
            'is_correct': row[2],
            'wrong_count': row[3],
            'mastered': row[4],
            'last_answer_time': row[5],
            'number': row[6],
            'stem': row[7],
            'option_a': row[8],
            'option_b': row[9],
            'option_c': row[10],
            'option_d': row[11],
            'correct_answer': row[12],
            'textbook': row[13] or '',
            'exam_id': row[14],
            'images': json.loads(row[15]) if row[15] else []
        })

    return {
        'items': items,
        'total': total,
        'page': page,
        'page_size': page_size,
        'total_pages': (total + page_size - 1) // page_size if total > 0 else 0
    }


def get_wrong_answer_stats(db, user_id):
    """获取错题统计"""
    cursor = db.cursor()

    # 总数和状态分布
    cursor.execute('''
        SELECT
            COUNT(*) AS total,
            SUM(CASE WHEN mastered = 0 THEN 1 ELSE 0 END) AS unmastered,
            SUM(CASE WHEN mastered = 1 THEN 1 ELSE 0 END) AS mastered_count
        FROM user_answers
        WHERE user_id = ? AND wrong_count > 0
    ''', (user_id,))
    row = cursor.fetchone()
    total = row[0] or 0
    unmastered = row[1] or 0
    mastered_count = row[2] or 0

    # 按教材分布
    cursor.execute('''
        SELECT q.textbook, COUNT(*) AS cnt
        FROM user_answers ua
        JOIN questions q ON ua.question_id = q.id
        WHERE ua.user_id = ? AND ua.wrong_count > 0
        GROUP BY q.textbook
        ORDER BY cnt DESC
    ''', (user_id,))
    by_textbook = {}
    for row in cursor.fetchall():
        tb = row[0] or '未分类'
        by_textbook[tb] = row[1]

    return {
        'total': total,
        'unmastered': unmastered,
        'mastered': mastered_count,
        'mastery_rate': round(mastered_count / total * 100, 1) if total > 0 else 0,
        'by_textbook': by_textbook
    }


def mark_mastered(db, user_id, question_id, mastered=1):
    """标记/取消标记错题为已攻克"""
    cursor = db.cursor()
    try:
        cursor.execute('''
            UPDATE user_answers
            SET mastered = ?
            WHERE user_id = ? AND question_id = ?
        ''', (mastered, user_id, question_id))
        db.commit()
        return cursor.rowcount > 0
    except Exception as e:
        db.rollback()
        raise e


def retry_wrong_answer(db, user_id, question_id, answer, is_correct):
    """重新作答错题（复用 save_user_answer，但也会更新 mastered 状态）"""
    # 如果答对了，自动标记为已攻克
    save_user_answer(db, user_id, question_id, answer, is_correct)
    if is_correct:
        mark_mastered(db, user_id, question_id, 1)
    return True


TEXTBOOK_KEYWORDS = {
    '必修一：分子与细胞': [
        '细胞膜', '细胞器', '线粒体', '叶绿体', '光合作用', '呼吸作用', '酶', 'ATP',
        '蛋白质', '核酸', '糖类', '脂质', '主动运输', '协助扩散', '渗透', '质壁分离',
        '细胞核', '细胞壁', '液泡', '核糖体', '内质网', '高尔基体', '溶酶体', '中心体',
        '细胞呼吸', '有氧呼吸', '无氧呼吸', '光反应', '暗反应', '卡尔文', '糖酵解',
        '氨基酸', '脱水缩合', '肽键', '双缩脲', '斐林', '苏丹', '扩散', '自由扩散',
        '胞吞', '胞吐', '选择透过性', '流动镶嵌', '生物膜', '分泌蛋白'
    ],
    '必修二：遗传与进化': [
        '遗传', '基因', 'DNA', 'RNA', '染色体', '减数分裂', '孟德尔', '分离定律',
        '自由组合', '突变', '进化', '自然选择', '伴性遗传', '转录', '翻译', '复制',
        '等位基因', '显性', '隐性', '纯合', '杂合', '基因型', '表现型', '同源染色体',
        '交叉互换', '基因重组', '染色体变异', '基因频率', '基因库', '物种形成',
        '生殖隔离', '共同进化', '遗传物质', '半保留复制', '中心法则', '密码子',
        '反密码子', 'mRNA', 'tRNA', '有丝分裂', '受精作用', '配子'
    ],
    '选修一：稳态与调节': [
        '稳态', '内环境', '神经调节', '体液调节', '激素', '免疫', '抗原', '抗体',
        '体温调节', '血糖调节', '反射', '突触', '甲状腺', '胰岛素', '胰高血糖素',
        '肾上腺素', '生长激素', '反馈调节', '分级调节', '非特异性免疫', '特异性免疫',
        '体液免疫', '细胞免疫', 'T细胞', 'B细胞', '淋巴因子', '过敏', '自身免疫',
        '水平衡', '水盐平衡', '渗透压', '感受器', '效应器', '传入神经', '传出神经',
        '突触小泡', '神经递质', '下丘脑', '垂体', '胰岛', '受体'
    ],
    '选修二：生物与环境': [
        '种群', '群落', '生态系统', '食物链', '食物网', '能量流动', '物质循环',
        '生态位', '竞争', '捕食', '生物多样性', '可持续发展', '种群密度', '出生率',
        '死亡率', '迁入率', '迁出率', '年龄组成', '性别比例', '增长型', '稳定型',
        '衰退型', 'J型', 'S型', 'K值', '环境容纳量', '垂直结构', '水平结构',
        '演替', '初生演替', '次生演替', '生产者', '消费者', '分解者', '营养级',
        '抵抗力稳定性', '恢复力稳定性', '温室效应', '酸雨', '富营养化', '生态环境'
    ],
    '选修三：生物技术与工程': [
        '基因工程', '限制酶', 'PCR', '载体', '细胞工程', '胚胎工程', '克隆',
        '发酵', '单克隆抗体', '植物组织培养', '质粒', 'DNA连接酶', '目的基因',
        '基因表达', '转基因', '动物细胞培养', '细胞融合', '杂交瘤', '胚胎移植',
        '体外受精', '胚胎分割', '干细胞', '全能性', '脱分化', '再分化', '愈伤组织',
        '微生物培养', '灭菌', '无菌操作', '选择培养基', '鉴别培养基', '生物反应器'
    ]
}


def categorize_textbook(stem, option_a='', option_b='', option_c='', option_d=''):
    """根据题干和选项关键词自动分类到教材"""
    if not stem:
        return ''

    full_text = f"{stem or ''} {option_a or ''} {option_b or ''} {option_c or ''} {option_d or ''}"

    scores = {}
    for textbook, keywords in TEXTBOOK_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw in full_text:
                score += 1
        if score > 0:
            scores[textbook] = score

    if scores:
        return max(scores, key=scores.get)
    return ''


def batch_categorize_questions(db):
    """批量给未分类的题目打上教材标签"""
    cursor = db.cursor()
    cursor.execute('SELECT id, stem, option_a, option_b, option_c, option_d FROM questions WHERE textbook IS NULL OR textbook = ""')
    rows = cursor.fetchall()

    updated = 0
    for row in rows:
        qid = row[0]
        textbook = categorize_textbook(row[1], row[2], row[3], row[4], row[5])
        if textbook:
            cursor.execute('UPDATE questions SET textbook = ? WHERE id = ?', (textbook, qid))
            updated += 1

    db.commit()
    return updated