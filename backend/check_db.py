import sqlite3

db = sqlite3.connect('forum.db')
cursor = db.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print('数据库中的表:')
for t in tables:
    print('  ', t[0])

cursor.execute('PRAGMA table_info(questions)')
cols = cursor.fetchall()
print('\nquestions表结构:')
for c in cols:
    print('  ', c[1], ':', c[2])

db.close()
