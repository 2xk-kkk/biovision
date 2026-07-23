import sqlite3

db = sqlite3.connect('forum.db')
cursor = db.cursor()

cursor.execute('SELECT COUNT(*) FROM questions')
total = cursor.fetchone()[0]
print('当前数据库中题目总数:', total)

cursor.execute('SELECT textbook, COUNT(*) FROM questions GROUP BY textbook')
result = cursor.fetchall()
print('\n各教材题目数量:')
for row in result:
    tb = row[0] if row[0] else '未分类'
    print('  ', tb, ':', row[1], '题')

cursor.execute('SELECT textbook, chapter, COUNT(*) FROM questions GROUP BY textbook, chapter ORDER BY textbook, chapter')
result = cursor.fetchall()
print('\n各章节目题数量:')
current_textbook = ''
for row in result:
    if row[0] != current_textbook:
        current_textbook = row[0]
        print('\n  ', current_textbook)
    print('    ', row[1], ':', row[2], '题')

db.close()
