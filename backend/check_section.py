import sqlite3

conn = sqlite3.connect('forum.db')

# 检查analysis值为'None'字符串的题目数量
cursor = conn.execute("""
    SELECT COUNT(*) FROM questions WHERE analysis = 'None'
""")
print(f'analysis值为"None"字符串的题目数量: {cursor.fetchone()[0]}')

# 检查第1节 细胞是生命活动的基本单位 中不同section的解析情况
cursor = conn.execute("""
    SELECT 
        section,
        COUNT(*) as total,
        SUM(CASE WHEN analysis IS NOT NULL AND analysis != '' AND analysis != 'None' THEN 1 ELSE 0 END) as has_analysis
    FROM questions 
    WHERE chapter = '第1章 走近细胞'
    GROUP BY section
    ORDER BY section
""")
print(f'\n第1章走近细胞各section解析统计:')
for row in cursor.fetchall():
    print(f'  Section: [{row[0] if row[0] else "空"}], 总题数: {row[1]}, 有解析: {row[2]}')

# 检查section='专项训练'的情况
cursor = conn.execute("""
    SELECT id, stem, answer, analysis, type
    FROM questions 
    WHERE chapter = '第1章 走近细胞'
    AND section = '专项训练'
    AND type = 'choice'
    LIMIT 5
""")
print(f'\n专项训练 选择题样例:')
for row in cursor.fetchall():
    has_a = row[3] and row[3].strip() and row[3] != 'None'
    print(f'  ID: {row[0]}, Answer: {row[2]}, HasAnalysis: {has_a}, Analysis: [{row[3][:60] if has_a else row[3]}]')

conn.close()
