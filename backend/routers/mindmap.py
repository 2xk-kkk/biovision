"""
思维导图 API 路由 — 为每本书生成结构化思维导图数据。
"""

import re
from fastapi import APIRouter
from database.db import get_db_connection
from utils.response import ApiResponse
from collections import defaultdict

router = APIRouter()

BOOKS = {
    "book1": {"name": "必修一：分子与细胞", "short": "必修1", "icon": "📘", "color": "#2c8c5a"},
    "book2": {"name": "必修二：遗传与进化", "short": "必修2", "icon": "📗", "color": "#1565c0"},
    "book3": {"name": "选择性必修一：稳态与调节", "short": "选必1", "icon": "📙", "color": "#6a1b9a"},
    "book4": {"name": "选择性必修二：生物与环境", "short": "选必2", "icon": "📕", "color": "#e65100"},
    "book5": {"name": "选择性必修三：生物技术与工程", "short": "选必3", "icon": "📓", "color": "#c62828"},
}

CATEGORY_COLORS = {
    "重点": "#e65100", "必考": "#c62828", "理解": "#1565c0",
    "记忆": "#6a1b9a", "概念": "#2c8c5a",
}

EMOJI_PATTERN = r'[📖🔬🧬🧪🔍💡📝🔥🎯⚡📚📗📘📙📕📓🔬🧬🧫⚖️🌿]'


# 章节名到排序序号的映射（用于修正数据库中章节号缺失的问题）
CHAPTER_ORDER = {
    # book1 必修一
    "走近细胞": 1, "组成细胞的分子": 2, "细胞的基本结构": 3,
    "细胞的物质输入和输出": 4, "细胞的能量供应和利用": 5, "细胞的生命历程": 6,
    # book2 必修二
    "遗传因子的发现": 1, "基因和染色体的关系": 2, "基因的本质": 3,
    "基因的表达": 4, "基因突变及其他变异": 5, "生物的进化": 6,
    # book3 选必1
    "人体的内环境与稳态": 1, "神经调节": 2, "体液调节": 3,
    "免疫调节": 4, "植物生命活动的调节": 5,
    # book4 选必2
    "种群及其动态": 1, "群落及其演替": 2, "生态系统及其稳定性": 3, "人与环境": 4,
    # book5 选必3
    "发酵工程": 1, "细胞工程": 2, "基因工程": 3, "生物技术的安全性与伦理问题": 4,
}


def _fix_chapter_name(chapter_raw: str) -> str:
    """修正章节名中的错误章节号，使用 CHAPTER_ORDER 映射的正确序号。"""
    # 提取章节名称部分（去除"第N章"前缀和后面的emoji/标注）
    name_part = re.sub(r'^第\d+章\s*', '', chapter_raw).strip()
    # 去除末尾的标注如"⭐ 核心章节"、"⭐ 最重要章节"
    name_part = re.sub(r'[⭐🔥📝🎯⚡]+.*$', '', name_part).strip()
    # 在 CHAPTER_ORDER 中查找正确的章节号
    for keyword, order in CHAPTER_ORDER.items():
        if keyword in name_part:
            return f"第{order}章 {keyword}"
    # 如果没找到映射，返回原名
    return chapter_raw


def _extract_chapter_number(chapter_name: str) -> int:
    """从章节名中提取章节序号用于排序。优先使用关键词映射。"""
    # 优先使用关键词映射（修正数据库中章节号错误的问题）
    for keyword, order in CHAPTER_ORDER.items():
        if keyword in chapter_name:
            return order

    # 尝试从"第N章"格式提取
    m = re.search(r'第(\d+)章', chapter_name)
    if m:
        return int(m.group(1))

    # 尝试中文数字
    cn_map = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8}
    m = re.search(r'第([一二三四五六七八])章', chapter_name)
    if m:
        return cn_map.get(m.group(1), 99)
    return 99


def _extract_section_display(section_name: str) -> str:
    """从节名提取简洁的显示名称。"""
    name = section_name
    # 去除开头的emoji、特殊符号等（保留中文、英文、数字）
    name = re.sub(r'^[^\u4e00-\u9fff\u3000-\u303f\uff00-\uffefa-zA-Z0-9]+', '', name).strip()
    # 去除序号前缀 (如 "第1节 ", "1. ", "-4节 ", "-3节 " 等)
    name = re.sub(r'^[-]?第?\d+\s*节?\s*', '', name).strip()
    # 如果含有 &，取主要部分
    if '&' in name:
        parts = [p.strip() for p in name.split('&')]
        name = parts[0]
    if not name:
        name = section_name
    return name


def _get_book_key(book_name: str) -> str:
    """从书籍全名推断book_key。"""
    for bk, info in BOOKS.items():
        if info["name"] == book_name:
            return bk
    mapping = {
        "必修一": "book1", "必修二": "book2",
        "必修三": "book3", "稳态": "book3", "调节": "book3",
        "生物与环境": "book4",
        "生物技术": "book5",
    }
    for keyword, bk in mapping.items():
        if keyword in book_name:
            return bk
    return book_name


def _build_mindmap_data():
    """从数据库构建所有书籍的思维导图数据。"""
    db = get_db_connection()
    try:
        cursor = db.cursor()
        cursor.execute("""
            SELECT book, chapter, section, section_name, label_text, category
            FROM knowledge_points
            ORDER BY book, chapter, section, id
        """)
        rows = cursor.fetchall()

        # book_key -> chapter_key(set) -> section_key -> [points]
        book_data = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

        for book, chapter, section, section_name, label_text, category in rows:
            book_key = _get_book_key(book)
            chapter_clean = chapter.strip()
            section_clean = (section or "").strip()
            section_name_clean = (section_name or "").strip()

            # 节的显示名
            section_display = _extract_section_display(
                section_name_clean if section_name_clean else section_clean
            )

            book_data[book_key][chapter_clean][section_clean].append({
                "label": label_text.strip(),
                "category": category,
                "color": CATEGORY_COLORS.get(category, "#546e7a"),
                "section_display": section_display,
                "chapter": chapter_clean,
                "section": section_display,
            })

        # 转换为输出格式
        result = {}
        BOOK_ORDER = ["book1", "book2", "book3", "book4", "book5"]

        for book_key in BOOK_ORDER:
            if book_key not in book_data:
                continue

            book_info = BOOKS[book_key]

            # 按章节序号排序
            chapter_keys = sorted(
                book_data[book_key].keys(),
                key=_extract_chapter_number
            )

            chapters_list = []
            for ch_key in chapter_keys:
                # 收集该章节所有节，并去重合并（相同display名的节合并）
                sections_map = {}
                for sec_key in book_data[book_key][ch_key]:
                    points = book_data[book_key][ch_key][sec_key]
                    sec_display = points[0]["section_display"] if points else sec_key
                    if sec_display not in sections_map:
                        sections_map[sec_display] = {
                            "name": sec_display,
                            "full_name": sec_key,
                            "points": [],
                        }
                    sections_map[sec_display]["points"].extend(points)

                sections_list = list(sections_map.values())
                # 按节内知识点数排序，或按原始顺序
                sections_list.sort(key=lambda s: (-len(s["points"]), s["name"]))

                chapters_list.append({
                    "name": _fix_chapter_name(ch_key),
                    "sections": sections_list,
                })

            total_points = sum(
                len(sec["points"])
                for ch in chapters_list
                for sec in ch["sections"]
            )

            result[book_key] = {
                "book": book_info["name"],
                "book_key": book_key,
                "icon": book_info["icon"],
                "color": book_info["color"],
                "chapters": chapters_list,
                "total_points": total_points,
            }

        return result
    finally:
        db.close()


@router.get("/mindmap/books")
def list_books():
    """获取所有书籍列表。"""
    data = _build_mindmap_data()
    books = []
    for bk, info in data.items():
        books.append({
            "book_key": bk,
            "name": info["book"],
            "icon": info["icon"],
            "color": info["color"],
            "chapters_count": len(info["chapters"]),
            "total_points": info["total_points"],
        })
    return ApiResponse.success(books)


@router.get("/mindmap/{book_key}")
def get_book_mindmap(book_key: str):
    """获取指定书籍的思维导图数据。"""
    data = _build_mindmap_data()
    if book_key in data:
        return ApiResponse.success(data[book_key])
    return ApiResponse.error(msg=f"未找到书籍: {book_key}")


@router.get("/mindmap")
def get_all_mindmaps():
    """获取所有书籍的思维导图数据。"""
    data = _build_mindmap_data()
    return ApiResponse.success(data)
