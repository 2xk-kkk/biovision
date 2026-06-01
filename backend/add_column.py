import sqlite3

try:
    conn = sqlite3.connect('forum.db')
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA table_info(user_interact)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'comment_id' not in columns:
        cursor.execute('ALTER TABLE user_interact ADD COLUMN comment_id INTEGER DEFAULT NULL')
        conn.commit()
        print('SUCCESS: Column comment_id added')
    else:
        print('INFO: Column comment_id already exists')
        
    conn.close()
except Exception as e:
    print(f'ERROR: {e}')
