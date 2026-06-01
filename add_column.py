import sqlite3

conn = sqlite3.connect('forum.db')
try:
    # 检查 comment_id 列是否已存在
    cursor = conn.execute("PRAGMA table_info(user_interact)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'comment_id' not in columns:
        conn.execute('ALTER TABLE user_interact ADD COLUMN comment_id INTEGER DEFAULT NULL')
        conn.commit()
        print('Column added successfully')
    else:
        print('Column already exists')
finally:
    conn.close()
