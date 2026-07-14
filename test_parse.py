import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from service.document_parser import parse_and_save

test_file = r"backend\uploads\exams\2022_全国甲卷_理综生物\2022年全国甲卷理综生物高考真题文档版（原卷含答案）.docx"

print(f"测试文件: {test_file}")
print(f"文件存在: {os.path.exists(test_file)}")

result = parse_and_save(test_file, custom_title="2022_全国甲卷_理综生物")
print(f"\n解析结果: {result}")

import sqlite3
conn = sqlite3.connect('backend/biovision.db')
cursor = conn.cursor()
cursor.execute("SELECT COUNT(*) FROM exams")
print(f"试卷数: {cursor.fetchone()[0]}")
cursor.execute("SELECT COUNT(*) FROM questions")
print(f"题目数: {cursor.fetchone()[0]}")
conn.close()
