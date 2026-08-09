"""
自动打标引擎 — 将题库中的每道题匹配到知识点。

通过关键词匹配 + 章节加权，为每道题的 knowledge_tags 字段
自动填入最匹配的知识点 ID 列表。
"""

import json
import re
import sys
from pathlib import Path

# 确保可以导入 PPT 模块
BASE_DIR = Path(__file__).resolve().parent.parent
_ppt_dir = BASE_DIR / 'PPT'
if str(_ppt_dir) not in sys.path:
    sys.path.insert(0, str(_ppt_dir))

from knowledge_reader import BOOK_NAMES, CHAPTER_NAMES

from model.knowledge_point import (
    get_all_knowledge_points,
    clear_knowledge_points,
    insert_knowledge_points,
)
from model.question import normalize_textbook_name
from database.db import get_db_connection

# 标点 / 选项标记正则
OPTION_LABEL_RE = re.compile(r'[A-D][.、．]\s*')
HTML_TAG_RE = re.compile(r'<[^>]+>')
PUNCTUATION_RE = re.compile(r'[，。！？、；：""''（）【】《》…—·（）\s]+')
MULTI_SPACE_RE = re.compile(r'\s{2,}')

# 匹配阈值
MIN_SCORE_THRESHOLD = 0.03   # 教材题的最低匹配分
MIN_SCORE_EXAM = 0.02        # 真题（无章节）的最低匹配分
MAX_TAGS_PER_QUESTION = 5


def _normalize_stem(stem: str) -> str:
    """标准化题干文本：去选项标记、HTML 标签、多余空白。"""
    text = OPTION_LABEL_RE.sub('', stem)
    text = HTML_TAG_RE.sub('', text)
    text = PUNCTUATION_RE.sub(' ', text)
    text = MULTI_SPACE_RE.sub(' ', text)
    return text.strip()


def _derive_chapter_key(textbook: str, chapter: str) -> str:
    """从教材名和章名推导 knowledge chapter_key（如 book1-ch1）。

    返回 '' 表示无法推导。
    """
    if not textbook or not chapter:
        return ''

    full_name = normalize_textbook_name(textbook)

    # textbook → bookN 映射
    textbook_to_book = {
        '必修一：分子与细胞': 'book1',
        '必修二：遗传与进化': 'book2',
        '选择性必修一：稳态与调节': 'book3',
        '选择性必修二：生物与环境': 'book4',
        '选择性必修三：生物技术与工程': 'book5',
    }
    # 也处理简称
    textbook_to_book.update({
        '选修一：稳态与调节': 'book3',
        '选修二：生物与环境': 'book4',
        '选修三：生物技术与工程': 'book5',
    })

    book = textbook_to_book.get(full_name, '')
    if not book:
        return ''

    # 提取章号
    m = re.search(r'第\s*(\d+)\s*章', chapter)
    if m:
        ch_num = int(m.group(1))
        return f"{book}-ch{ch_num}"

    return ''


def tag_single_question(stem: str, textbook: str, chapter: str, section: str,
                        all_kp_by_chapter: dict[str, list[dict]],
                        all_kp_flat: list[dict]) -> list[list]:
    """为单道题匹配知识点标签。

    Args:
        stem: 题干文本
        textbook: 教材名
        chapter: 章节名（如 "第1章 走近细胞"）
        section: 节名
        all_kp_by_chapter: {chapter_key: [kp_dict, ...]}
        all_kp_flat: 所有知识点（兜底用）

    Returns:
        [[kp_id, score], ...] 排序后的 top-5 标签
    """
    stem_norm = _normalize_stem(stem)
    if not stem_norm:
        return []

    chapter_key = _derive_chapter_key(textbook, chapter)
    has_chapter = bool(chapter_key and chapter)

    # 确定候选知识点池
    if has_chapter and chapter_key in all_kp_by_chapter:
        # 教材题：优先同章知识点，也包含同教材其他章作为兜底
        candidates = all_kp_by_chapter[chapter_key]
        # 同教材其他章也加入候选（给关键词匹配更多可能）
        book_prefix = chapter_key.rsplit('-', 1)[0]
        for ck, kps in all_kp_by_chapter.items():
            if ck != chapter_key and ck.startswith(book_prefix):
                candidates.extend(kps)
    else:
        # 真题或无章节数据：扫描所有知识点
        candidates = all_kp_flat

    # 短文题干（< 15 字符）降低阈值
    threshold = MIN_SCORE_THRESHOLD if has_chapter else MIN_SCORE_EXAM
    if len(stem_norm) < 15:
        threshold *= 0.5  # 短文更宽松

    best_matches = []

    for kp in candidates:
        key_terms = kp.get('key_terms', [])
        if not key_terms:
            continue

        # 统计匹配的关键词
        match_count = 0
        weighted_matches = 0.0
        for idx, term in enumerate(key_terms):
            if term in stem_norm:
                match_count += 1
                # 前几个词是粗体词，权重更高
                weight = 2.0 if idx < len(kp.get('strong_terms', [])) + 1 else 1.0
                weighted_matches += weight * len(term)

        if match_count == 0:
            continue

        # 基础分 = 加权匹配长度 / 题干长度
        raw_score = weighted_matches / max(len(stem_norm), 1)

        # 上下文加权
        if has_chapter:
            # 同章加权
            if kp.get('chapter') and chapter and kp['chapter'] == chapter:
                raw_score *= 1.5
            # 同节加权（更高）
            if section and kp.get('section') and section in kp['section']:
                raw_score *= 1.8

        # 分类加权
        if kp.get('category') in ('必考', '重点'):
            raw_score *= 1.2

        threshold = MIN_SCORE_THRESHOLD if has_chapter else MIN_SCORE_EXAM
        if raw_score > threshold:
            best_matches.append((kp['id'], round(raw_score, 4)))

    # 按分数降序，取 top-N
    best_matches.sort(key=lambda x: x[1], reverse=True)
    return best_matches[:MAX_TAGS_PER_QUESTION]


def run_auto_tagging(db=None) -> dict:
    """为所有题目自动打标，更新 knowledge_tags 字段。

    Args:
        db: 可选，已存在的数据库连接；若为 None 则自动获取

    Returns:
        {total: 总题数, tagged: 已打标数, untagged: 未打标数}
    """
    should_close = False
    if db is None:
        db = get_db_connection()
        should_close = True

    try:
        cursor = db.cursor()

        # 加载所有知识点
        all_kps = get_all_knowledge_points(db)
        if not all_kps:
            return {'total': 0, 'tagged': 0, 'untagged': 0,
                    'error': '知识库为空，请先运行 init_knowledge_points'}

        # 按 chapter_key 分组
        all_kp_by_chapter = {}
        for kp in all_kps:
            ck = kp['chapter_key']
            if ck not in all_kp_by_chapter:
                all_kp_by_chapter[ck] = []
            all_kp_by_chapter[ck].append(kp)

        # 加载所有题目
        cursor.execute('''
            SELECT id, stem, textbook, chapter, section
            FROM questions
        ''')
        questions = cursor.fetchall()

        tagged = 0
        untagged = 0

        for q in questions:
            qid, stem, textbook, chapter, section = q
            tags = tag_single_question(
                stem or '', textbook or '', chapter or '', section or '',
                all_kp_by_chapter, all_kps
            )

            tags_json = json.dumps(tags, ensure_ascii=False) if tags else '[]'
            cursor.execute(
                'UPDATE questions SET knowledge_tags = ? WHERE id = ?',
                (tags_json, qid)
            )

            if tags:
                tagged += 1
            else:
                untagged += 1

        db.commit()

        return {
            'total': len(questions),
            'tagged': tagged,
            'untagged': untagged,
            'coverage': round(tagged / len(questions) * 100, 1) if questions else 0,
            'knowledge_points': len(all_kps),
        }

    except Exception as e:
        db.rollback()
        raise e
    finally:
        if should_close:
            db.close()


if __name__ == '__main__':
    # 直接运行可测试打标效果
    from service.knowledge_parser import parse_all_knowledge_files

    db = get_db_connection()

    # 先加载知识点
    points = parse_all_knowledge_files()
    print(f"解析到 {len(points)} 条知识点")

    clear_knowledge_points(db)
    inserted = insert_knowledge_points(db, points)
    print(f"已插入 {inserted} 条")

    # 打标
    result = run_auto_tagging(db)
    print(f"\n打标结果: {result}")

    # 抽查
    cursor = db.cursor()
    cursor.execute("""
        SELECT id, stem, knowledge_tags FROM questions
        WHERE knowledge_tags != '[]'
        ORDER BY RANDOM() LIMIT 5
    """)
    for row in cursor.fetchall():
        tags = json.loads(row[2])
        print(f"\n  Q{row[0]}: {row[1][:60]}...")
        # 查询知识点名称
        for t in tags[:3]:
            kp = cursor.execute(
                'SELECT label_text, category FROM knowledge_points WHERE id = ?',
                (t[0],)
            ).fetchone()
            if kp:
                print(f"    [{kp[1]}] {kp[0][:60]}...  (score={t[1]})")

    db.close()
