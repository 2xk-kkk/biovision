# -*- coding: utf-8 -*-
"""
模拟试卷批量导入脚本

用法：
    python scripts/import_mock_exams.py <json文件路径>

JSON 格式示例（每个元素一套试卷）：
[
  {
    "name": "2025_人大附中_月考",
    "questions": [
      {
        "number": 1,
        "stem": "下列关于细胞结构的叙述，正确的是（ ）",
        "options": {"A": "...", "B": "...", "C": "...", "D": "..."},
        "answer": "A",
        "analysis": "解析文字（可选）"
      }
    ]
  }
]

name 命名规范（与前端试卷练习页一致）：
    年份_学校_类型，例如 2025_人大附中_月考 / 2026_衡水中学_期末
    学校：人大附中/北京四中/上海中学/华师大二附中/南京外国语/杭二中/华师一附中/成都七中/深圳中学/衡水中学
    类型：月考/期中/期末/模拟考/联考

运行后：
    1. 在 uploads/exams/{name}/ 下生成 questions.json（试卷题目留档，也让目录非空）
    2. 写入 exams 表（若已存在则更新题目数量）
    3. 写入 questions 表（同套同题号覆盖更新，可重复运行）
"""
import json
import os
import sqlite3
import sys

# Windows 控制台可能是 GBK 编码，强制 UTF-8 输出，避免特殊字符报错
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXAM_DIR = os.path.join(BASE_DIR, "uploads", "exams")
DB_PATH = os.path.join(BASE_DIR, "forum.db")


def get_question_columns(cursor):
    """返回 questions 表实际存在的列，避免写不存在的可选列报错。"""
    cursor.execute("PRAGMA table_info(questions)")
    return [row[1] for row in cursor.fetchall()]


def import_exams(json_path):
    if not os.path.exists(json_path):
        print(f"错误：文件不存在 {json_path}")
        sys.exit(1)

    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    if not isinstance(data, list):
        print("错误：JSON 顶层必须是数组（试卷列表）")
        sys.exit(1)

    os.makedirs(EXAM_DIR, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cols = get_question_columns(cursor)

    total_exams = 0
    total_questions = 0

    for exam in data:
        name = exam.get("name", "").strip()
        questions = exam.get("questions", [])
        if not name or not questions:
            print(f"跳过：缺少 name 或 questions（{name or '未命名'}）")
            continue

        # 1. 建立试卷目录，题目存成 questions.json 留档
        folder = os.path.join(EXAM_DIR, name)
        os.makedirs(folder, exist_ok=True)
        with open(os.path.join(folder, "questions.json"), "w", encoding="utf-8") as f:
            json.dump(questions, f, ensure_ascii=False, indent=2)

        # 2. 写入 exams 表
        cursor.execute(
            "INSERT INTO exams (name, file_name, question_count) VALUES (?, ?, ?) "
            "ON CONFLICT(name) DO UPDATE SET question_count = excluded.question_count",
            (name, "questions.json", len(questions)),
        )
        cursor.execute("SELECT id FROM exams WHERE name = ?", (name,))
        exam_id = cursor.fetchone()[0]

        # 3. 写入 questions 表
        for q in questions:
            number = q.get("number")
            stem = q.get("stem", "")
            options = q.get("options", {}) or {}
            answer = q.get("answer", "")

            values = [exam_id, number, stem,
                      options.get("A", ""), options.get("B", ""),
                      options.get("C", ""), options.get("D", ""), answer]

            # 可选字段：仅当列存在时才写入
            extra_cols = []
            extra_vals = []
            if "type" in cols:
                extra_cols.append("type")
                # 题目级 type 优先（choice/essay/fill），否则回退到试卷级 type（模拟考/月考等）
                extra_vals.append(q.get("type") or exam.get("type", ""))
            if "analysis" in cols:
                extra_cols.append("analysis")
                extra_vals.append(q.get("analysis", ""))

            col_list = ["exam_id", "number", "stem", "option_a", "option_b", "option_c", "option_d", "answer"] + extra_cols
            placeholders = ",".join(["?"] * len(col_list))
            cursor.execute(
                f"INSERT INTO questions ({','.join(col_list)}) VALUES ({placeholders}) "
                "ON CONFLICT(exam_id, number) DO UPDATE SET "
                "stem = excluded.stem, option_a = excluded.option_a, option_b = excluded.option_b, "
                "option_c = excluded.option_c, option_d = excluded.option_d, answer = excluded.answer",
                values + extra_vals,
            )
            total_questions += 1

        conn.commit()
        total_exams += 1
        print(f"[OK] {name}: {len(questions)} 题")

    conn.close()
    print(f"\n完成：导入 {total_exams} 套试卷，共 {total_questions} 道题")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    import_exams(sys.argv[1])
