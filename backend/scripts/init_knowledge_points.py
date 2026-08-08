"""
知识库初始化脚本 — 一次性执行，完成以下操作：

1. 解析 25 个知识 HTML 文件
2. 写入 knowledge_points 表
3. 为 3839 道题自动打标
4. 输出统计摘要
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from database.db import get_db_connection
from model.knowledge_point import clear_knowledge_points, insert_knowledge_points, get_all_knowledge_points
from service.knowledge_parser import parse_all_knowledge_files
from service.knowledge_tagging import run_auto_tagging


def main():
    print("=" * 60)
    print("  BioVision 知识库初始化")
    print("=" * 60)

    db = get_db_connection()

    try:
        # Step 1: 解析 HTML 文件
        print("\n[1/3] 解析知识 HTML 文件...")
        points = parse_all_knowledge_files()
        print(f"  ✓ 共解析 {len(points)} 条知识点")

        # 统计
        from collections import Counter
        cat_counts = Counter(p['category'] for p in points)
        print(f"     分类: {dict(cat_counts)}")
        book_counts = Counter(p['book'] for p in points)
        for book, cnt in book_counts.items():
            print(f"     {book}: {cnt} 条")

        # Step 2: 写入数据库
        print("\n[2/3] 写入 knowledge_points 表...")
        clear_knowledge_points(db)
        inserted = insert_knowledge_points(db, points)
        print(f"  ✓ 已写入 {inserted} 条")

        # 验证
        stored = get_all_knowledge_points(db)
        print(f"  ✓ 验证: 数据库中有 {len(stored)} 条")

        # Step 3: 自动打标
        print("\n[3/3] 自动打标所有题目...")
        result = run_auto_tagging(db=db)
        print(f"  ✓ 总题数: {result['total']}")
        print(f"  ✓ 已打标: {result['tagged']}")
        print(f"  ✓ 未打标: {result['untagged']}")
        print(f"  ✓ 覆盖率: {result['coverage']}%")

        print("\n" + "=" * 60)
        print("  ✅ 知识库初始化完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n  ❌ 初始化失败: {e}")
        raise
    finally:
        db.close()


if __name__ == '__main__':
    main()
