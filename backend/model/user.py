#用户功能数据库操作
from utils.crypto import hash_password

#注册
def register(db, username, password, telephone):
    cursor = db.cursor()
    cursor.execute("insert into users(username,password,telephone) values(?,?,?)",(username,hash_password(password), telephone))
    db.commit()
    return cursor.lastrowid

#根据用户名获取用户信息
def get_user_by_username(db, username):
    cursor = db.cursor()
    cursor.execute("select id,username,password from users where username=?",(username,))
    result = cursor.fetchone() 
    return result

#注销用户
def delete_user(db, username):
    cursor = db.cursor()
    cursor.execute("delete from users where username=?",(username,))
    db.commit()
   

#修改密码
def change_password(db, username, new_password):
    cursor = db.cursor()
    cursor.execute("update users set password=? where username=?",(hash_password(new_password),username))
    db.commit()
    

#查看数据库用户是否存在
def user_exists(db, username):
    cursor = db.cursor()
    cursor.execute("select true from users where username=?",(username,))
    
    return cursor.fetchone() is not None

#修改用户名
def update_username(db, user_id, new_username):
    cursor = db.cursor()
    cursor.execute("update users set username=? where id=?",(new_username, user_id))
    db.commit()
    return cursor.rowcount > 0

#更新头像
def update_avatar(db, user_id, avatar_data):
    cursor = db.cursor()
    cursor.execute("update users set avatar=? where id=?",(avatar_data, user_id))
    db.commit()
    return cursor.rowcount > 0

#根据用户ID获取用户信息（包含头像和简介）
def get_user_by_id(db, user_id):
    cursor = db.cursor()
    cursor.execute("select id, username, avatar, introduction from users where id=?",(user_id,))
    result = cursor.fetchone()
    return result

#更新个人简介
def update_introduction(db, user_id, introduction):
    cursor = db.cursor()
    cursor.execute("update users set introduction=? where id=?",(introduction, user_id))
    db.commit()
    return cursor.rowcount > 0

#增加获赞数
def increment_like_count(db, user_id):
    cursor = db.cursor()
    cursor.execute("update users set like_count = like_count + 1 where id=?",(user_id,))
    db.commit()
    return cursor.rowcount > 0

#增加粉丝数
def increment_follower_count(db, user_id):
    cursor = db.cursor()
    cursor.execute("update users set follower_count = follower_count + 1 where id=?",(user_id,))
    db.commit()
    return cursor.rowcount > 0

#减少粉丝数
def decrement_follower_count(db, user_id):
    cursor = db.cursor()
    cursor.execute("update users set follower_count = max(0, follower_count - 1) where id=?",(user_id,))
    db.commit()
    return cursor.rowcount > 0

#增加关注数
def increment_following_count(db, user_id):
    cursor = db.cursor()
    cursor.execute("update users set following_count = following_count + 1 where id=?",(user_id,))
    db.commit()
    return cursor.rowcount > 0

#减少关注数
def decrement_following_count(db, user_id):
    cursor = db.cursor()
    cursor.execute("update users set following_count = max(0, following_count - 1) where id=?",(user_id,))
    db.commit()
    return cursor.rowcount > 0

#增加浏览量（看过我的）
def increment_view_count(db, user_id):
    cursor = db.cursor()
    cursor.execute("update users set view_count = view_count + 1 where id=?",(user_id,))
    db.commit()
    return cursor.rowcount > 0

#获取用户统计数据
def get_user_stats(db, user_id):
    cursor = db.cursor()
    
    # 获取用户基本信息
    cursor.execute("select follower_count, following_count, view_count from users where id=?",(user_id,))
    user_result = cursor.fetchone()
    
    if not user_result:
        return None
    
    # 统计用户所有帖子的获赞数
    cursor.execute("select COALESCE(SUM(like_count), 0) from posts where user_id=?",(user_id,))
    total_likes = cursor.fetchone()[0] or 0
    
    # 统计用户发布的帖子数
    cursor.execute("select COALESCE(COUNT(*), 0) from posts where user_id=?",(user_id,))
    post_count = cursor.fetchone()[0] or 0
    
    return {
        "like_count": total_likes,
        "follower_count": user_result[0] or 0,
        "following_count": user_result[1] or 0,
        "view_count": user_result[2] or 0,
        "post_count": post_count
    }

#关注用户
def follow_user(db, follower_id, following_id):
    cursor = db.cursor()
    try:
        cursor.execute("insert into user_follow(follower_id, following_id) values(?,?)",(follower_id, following_id))
        db.commit()
        return True
    except:
        db.rollback()
        return False

#取消关注
def unfollow_user(db, follower_id, following_id):
    cursor = db.cursor()
    cursor.execute("delete from user_follow where follower_id=? and following_id=?",(follower_id, following_id))
    db.commit()
    return cursor.rowcount > 0

#检查是否已关注
def is_following(db, follower_id, following_id):
    cursor = db.cursor()
    cursor.execute("select true from user_follow where follower_id=? and following_id=?",(follower_id, following_id))
    return cursor.fetchone() is not None

#获取粉丝列表
def get_followers(db, user_id):
    cursor = db.cursor()
    cursor.execute("select u.id, u.username, u.avatar from user_follow f join users u on f.follower_id = u.id where f.following_id=?",(user_id,))
    return cursor.fetchall()

#获取关注列表
def get_following(db, user_id):
    cursor = db.cursor()
    cursor.execute("select u.id, u.username, u.avatar from user_follow f join users u on f.following_id = u.id where f.follower_id=?",(user_id,))
    return cursor.fetchall()