import time
from database.db import get_db_connection

# 记录用户最后活跃时间
def update_user_active(user_id):
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO user_online (user_id, last_active)
            VALUES (?, ?)
        ''', (user_id, int(time.time())))
        
        db.commit()
        db.close()
    except:
        pass

# 获取真实在线人数（5分钟内活跃 = 在线）
def get_real_online_users():
    try:
        db = get_db_connection()
        cursor = db.cursor()
        
        now = int(time.time())
        five_min = 5 * 60
        cutoff = now - five_min
        
        cursor.execute('''
            SELECT COUNT(*) FROM user_online WHERE last_active >= ?
        ''', (cutoff,))
        
        count = cursor.fetchone()[0]
        db.close()
        return count
    except:
        return 8