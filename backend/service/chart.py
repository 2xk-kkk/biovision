# backend/service/chart.py
from database.db import get_db_connection
from utils.response import ApiResponse
from datetime import datetime, timedelta  


def get_forum_stats():
    db = get_db_connection()
    try:
        cursor = db.cursor()

        # 用户总数
        cursor.execute("SELECT COUNT(*) FROM users")
        total_users = cursor.fetchone()[0]

        # 帖子总数
        cursor.execute("SELECT COUNT(*) FROM posts")
        total_posts = cursor.fetchone()[0]

        # 评论总数（没有就给0）
        try:
            cursor.execute("SELECT COUNT(*) FROM comments")
            total_comments = cursor.fetchone()[0]
        except:
            total_comments = 0

        # 在线用户（暂时固定）

        def get_real_online_users():
            try:
                import time
                db = get_db_connection()
                cursor = db.cursor()
                now = int(time.time())
                cutoff = now - 5 * 60  # 5分钟内

                cursor.execute("SELECT COUNT(*) FROM user_online WHERE last_active >= ?", (cutoff,))
                count = cursor.fetchone()[0]
                db.close()
                return count if count > 0 else 1
            except:
                return 1

        online_users = get_real_online_users()



        
        today = datetime.now().date()
        seven_days_ago = today - timedelta(days=6)

        activity_data = [0] * 7
        date_labels = []  # 用来存真实日期

        # 生成近7天日期列表 ['2026-05-12', '2026-05-13', ...]
        for i in range(7):
            date = seven_days_ago + timedelta(days=i)
            date_labels.append(date.strftime("%Y-%m-%d"))


        try:
            cursor.execute("""
                SELECT DATE(create_at) AS post_date, COUNT(*) AS cnt
                FROM posts
                WHERE DATE(create_at) >= ?
                GROUP BY DATE(create_at)
                ORDER BY DATE(create_at)
            """, (seven_days_ago,))

            rows = cursor.fetchall()
            for row in rows:
                d_str = row[0]
                cnt = row[1]
                try:
                    d = datetime.strptime(d_str, "%Y-%m-%d").date()
                    idx = (d - seven_days_ago).days
                    if 0 <= idx < 7:
                        activity_data[idx] = cnt
                except:
                    pass
        except:
            activity_data = [0, 0, 0, 0, 0, 0, 0]     

        return ApiResponse.success({
            "total_users": total_users,
            "total_posts": total_posts,
            "total_comments": total_comments,
            "online_users": online_users,
            "activity": activity_data,
            "activity_dates": date_labels
        })
    except Exception as e:
        return ApiResponse.error(msg="获取统计失败")
    finally:
        db.close()