"""
知识点数据模型 — knowledge_points 表的 CRUD 操作。
"""

import json


def insert_knowledge_points(db, points: list[dict]) -> int:
    """批量插入知识点记录。

    Args:
        db: 数据库连接
        points: 知识点字典列表

    Returns:
        插入的行数
    """
    cursor = db.cursor()
    count = 0
    try:
        for p in points:
            cursor.execute('''
                INSERT OR REPLACE INTO knowledge_points
                (chapter_key, book, chapter, section, section_name,
                 label_text, category, key_terms, data_id, file_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                p['chapter_key'],
                p['book'],
                p['chapter'],
                p.get('section', ''),
                p.get('section_name', ''),
                p['label_text'],
                p['category'],
                json.dumps(p['key_terms'], ensure_ascii=False),
                p.get('data_id'),
                p.get('file_path', ''),
            ))
            count += 1
        db.commit()
        return count
    except Exception as e:
        db.rollback()
        raise e


def clear_knowledge_points(db) -> int:
    """清空知识点表，返回删除行数。"""
    cursor = db.cursor()
    cursor.execute('DELETE FROM knowledge_points')
    db.commit()
    return cursor.rowcount


def get_all_knowledge_points(db) -> list[dict]:
    """获取所有知识点。

    Returns:
        list of dict，含 id, chapter_key, book, chapter, section,
        section_name, label_text, category, key_terms (list), data_id, file_path
    """
    cursor = db.cursor()
    cursor.execute('''
        SELECT id, chapter_key, book, chapter, section, section_name,
               label_text, category, key_terms, data_id, file_path
        FROM knowledge_points
        ORDER BY chapter_key, id
    ''')
    results = []
    for row in cursor.fetchall():
        try:
            key_terms = json.loads(row[8]) if row[8] else []
        except (json.JSONDecodeError, TypeError):
            key_terms = []
        results.append({
            'id': row[0],
            'chapter_key': row[1],
            'book': row[2],
            'chapter': row[3],
            'section': row[4] or '',
            'section_name': row[5] or '',
            'label_text': row[6],
            'category': row[7],
            'key_terms': key_terms,
            'data_id': row[9],
            'file_path': row[10] or '',
        })
    return results


def get_knowledge_points_by_chapter_key(db, chapter_key: str) -> list[dict]:
    """按章节 key 查询知识点（如 book1-ch1）。"""
    cursor = db.cursor()
    cursor.execute('''
        SELECT id, chapter_key, book, chapter, section, section_name,
               label_text, category, key_terms, data_id, file_path
        FROM knowledge_points
        WHERE chapter_key = ?
        ORDER BY id
    ''', (chapter_key,))
    results = []
    for row in cursor.fetchall():
        try:
            key_terms = json.loads(row[8]) if row[8] else []
        except (json.JSONDecodeError, TypeError):
            key_terms = []
        results.append({
            'id': row[0],
            'chapter_key': row[1],
            'book': row[2],
            'chapter': row[3],
            'section': row[4] or '',
            'section_name': row[5] or '',
            'label_text': row[6],
            'category': row[7],
            'key_terms': key_terms,
            'data_id': row[9],
            'file_path': row[10] or '',
        })
    return results


def get_knowledge_point_by_id(db, kp_id: int) -> dict | None:
    """按 ID 获取单个知识点。"""
    cursor = db.cursor()
    cursor.execute('''
        SELECT id, chapter_key, book, chapter, section, section_name,
               label_text, category, key_terms, data_id, file_path
        FROM knowledge_points
        WHERE id = ?
    ''', (kp_id,))
    row = cursor.fetchone()
    if not row:
        return None
    try:
        key_terms = json.loads(row[8]) if row[8] else []
    except (json.JSONDecodeError, TypeError):
        key_terms = []
    return {
        'id': row[0],
        'chapter_key': row[1],
        'book': row[2],
        'chapter': row[3],
        'section': row[4] or '',
        'section_name': row[5] or '',
        'label_text': row[6],
        'category': row[7],
        'key_terms': key_terms,
        'data_id': row[9],
        'file_path': row[10] or '',
    }


def get_knowledge_points_by_ids(db, kp_ids: list[int]) -> dict[int, dict]:
    """批量按 ID 查询知识点，返回 {id: dict} 映射。"""
    if not kp_ids:
        return {}
    placeholders = ','.join('?' for _ in kp_ids)
    cursor = db.cursor()
    cursor.execute(f'''
        SELECT id, chapter_key, book, chapter, section, section_name,
               label_text, category, key_terms, data_id, file_path
        FROM knowledge_points
        WHERE id IN ({placeholders})
    ''', kp_ids)
    results = {}
    for row in cursor.fetchall():
        try:
            key_terms = json.loads(row[8]) if row[8] else []
        except (json.JSONDecodeError, TypeError):
            key_terms = []
        results[row[0]] = {
            'id': row[0],
            'chapter_key': row[1],
            'book': row[2],
            'chapter': row[3],
            'section': row[4] or '',
            'section_name': row[5] or '',
            'label_text': row[6],
            'category': row[7],
            'key_terms': key_terms,
            'data_id': row[9],
            'file_path': row[10] or '',
        }
    return results


def get_question_knowledge_tags(db, question_id: int) -> list[tuple]:
    """获取题目的知识点标签。

    Returns:
        list of (kp_id, score) tuples，若为空返回 []
    """
    cursor = db.cursor()
    cursor.execute('SELECT knowledge_tags FROM questions WHERE id = ?', (question_id,))
    row = cursor.fetchone()
    if not row or not row[0]:
        return []
    try:
        tags = json.loads(row[0])
        if isinstance(tags, list) and tags and isinstance(tags[0], list):
            return [(t[0], t[1]) for t in tags]
        return []
    except (json.JSONDecodeError, TypeError):
        return []
