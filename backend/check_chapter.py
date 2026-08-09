import sqlite3

conn = sqlite3.connect('forum.db')
cursor = conn.cursor()

# 检查遗传因子章节的题目
print("=== 遗传因子章节题目解析情况 ===")
cursor.execute("""
    SELECT id, stem, chapter, section, answer, analysis
    FROM questions 
    WHERE chapter LIKE '%遗传因子%'
    LIMIT 15
""")

for r in cursor.fetchall():
    has_analysis = "✅ 有解析" if r[5] and r[5] != 'None' and r[5] != '' else "❌ 无解析"
    print(f"ID={r[0]} | {r[2]} | {r[3]} | {has_analysis}")
    print(f"  题干: {r[1][:50]}...")
    print(f"  解析: {r[5][:80] if r[5] and r[5] != 'None' else '无'}...")
    print()

# 统计
cursor.execute("""
    SELECT 
        COUNT(*) as total,
        SUM(CASE WHEN analysis IS NOT NULL AND analysis != '' AND analysis != 'None' THEN 1 ELSE 0 END) as with_analysis
    FROM questions 
    WHERE chapter LIKE '%遗传因子%'
""")
r = cursor.fetchone()
print(f"统计: 共{r[0]}题, 有解析{r[1]}题")

# 再检查孟德尔的豌豆杂交实验
print("\n=== 孟德尔豌豆杂交实验 ===")
cursor.execute("""
    SELECT id, stem, chapter, section, answer, analysis
    FROM questions 
    WHERE section LIKE '%孟德尔%'
    LIMIT 10
""")
for r in cursor.fetchall():
    has_analysis = "✅ 有解析" if r[5] and r[5] != 'None' and r[5] != '' else "❌ 无解析"
    print(f"ID={r[0]} | {r[3]} | {has_analysis}")
    print(f"  题干: {r[1][:50]}...")

conn.close()
