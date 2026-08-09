import sqlite3

conn = sqlite3.connect('forum.db')

# 搜索这道题
question_stem = '下列关于病毒的叙述，错误的是'
cursor = conn.execute(f"""
    SELECT id, stem, answer, analysis, type, textbook, chapter, section 
    FROM questions 
    WHERE stem LIKE '%{question_stem}%'
""")
print(f'搜索题目: {question_stem}...')
rows = cursor.fetchall()
if rows:
    for row in rows:
        print(f'ID: {row[0]}')
        print(f'Stem: {row[1]}')
        print(f'Answer: {row[2]}')
        has_analysis = row[3] and row[3].strip() and row[3] != 'None'
        print(f'Analysis: [{row[3]}]')
        print(f'HasAnalysis: {has_analysis}')
        print(f'Type: {row[4]}')
        print(f'Textbook: {row[5]}')
        print(f'Chapter: {row[6]}')
        print(f'Section: {row[7]}')
        print('---')
else:
    print('未找到题目')
    # 检查section=第1节 细胞是生命活动的基本单位的选择题
    cursor = conn.execute("""
        SELECT id, stem, answer, analysis, type, chapter, section
        FROM questions 
        WHERE chapter = '第1章 走近细胞' 
        AND section = '第1节 细胞是生命活动的基本单位'
        AND type = 'choice'
        LIMIT 20
    """)
    print('\n第1节 细胞是生命活动的基本单位 的选择题:')
    for row in cursor.fetchall():
        has_analysis = row[3] and row[3].strip() and row[3] != 'None'
        print(f'ID: {row[0]}, Stem: {row[1][:60]}..., Answer: {row[2]}, HasAnalysis: {has_analysis}')

conn.close()
