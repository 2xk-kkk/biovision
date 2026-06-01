#用户功能业务逻辑
from utils.crypto import verify_password
from model.user import register, get_user_by_username, delete_user, change_password, user_exists, update_username, update_avatar, get_user_by_id, update_introduction, get_user_stats, follow_user, unfollow_user, is_following, increment_view_count, increment_like_count, increment_follower_count, decrement_follower_count, increment_following_count, decrement_following_count, get_followers, get_following, get_post_likers 
from database.db import get_db_connection
from utils.jwt_utils import generate_jwt
from utils.response import ApiResponse
import re

#用户注册
def register_user(username, password, telephone):
    if not username or not password:
        return ApiResponse.error(msg="用户名和密码不能为空")

    if len(password) < 6 or len(password) > 20:
        return ApiResponse.error(msg="密码长度必须在6到20个字符之间")
    if not re.search(r'[A-Za-z]', password) or not re.search(r'[0-9]', password):
        return ApiResponse.error(msg="密码必须同时包含字母和数字")
    if not telephone:
        return ApiResponse.error(msg="电话号码不能为空")
    if not re.search(r'^[0-9]{7,15}$', telephone):
        return ApiResponse.error(msg="电话号码必须在7到15个数字之间")
    db = get_db_connection()
    existing_user = get_user_by_username(db, username)
    if existing_user is not None:
        return ApiResponse.error(msg="用户名已存在")
    try:
        user_id=register(db, username, password, telephone)
        token = generate_jwt(user_id, username)
        return ApiResponse.success(
            data={"token": token,
                  'user_id': user_id,
                  'username': username,
                  'telephone': telephone
                  }, msg="注册成功")
    except Exception as e:
        return ApiResponse.error(msg=f"注册失败: {str(e)}")
    finally:
        db.close()
    
    
#用户登录
def login_user(username, password):
    db = get_db_connection()
    if not username or not password:
        return ApiResponse.error(msg="用户名和密码不能为空")
    try:
        if not user_exists(db, username):
            return ApiResponse.error(msg="用户不存在")
        user_id,user_name,hashed_password = get_user_by_username(db, username)
        if verify_password(password, hashed_password):
            import time
            cursor = db.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO user_online (user_id, last_active) VALUES (?, ?)",
                (user_id, int(time.time()))
            )
            db.commit()

            token = generate_jwt(user_id, user_name)
            return ApiResponse.success(
                data={"token": token,
                      'user_id': user_id,
                      'username': user_name,
                      },
                msg="登录成功"
            )
        else:
            return ApiResponse.error(msg="密码错误")
    finally:
        db.close()
    

#用户注销
def delete_user_account(username):
    db = get_db_connection()
    try:
        if not user_exists(db, username):
            return ApiResponse.error(msg="用户不存在")  
        else:
            delete_user(db, username)
            return ApiResponse.success(msg="用户注销成功")
    except Exception as e:
        return ApiResponse.error(msg=f"用户注销失败: {str(e)}")
    finally:
        db.close()
    
#修改密码
def change_user_password(userid, old_password, new_password):
    if not new_password:
        return ApiResponse.error(msg="新密码不能为空")
    if len(new_password) < 6 or len(new_password) > 20:
        return ApiResponse.error(msg="新密码长度必须在6到20个字符之间")
    if not re.search(r'[A-Za-z]', new_password) or not re.search(r'[0-9]', new_password):
        return ApiResponse.error(msg="新密码必须同时包含字母和数字")
    if old_password == new_password:
        return ApiResponse.error(msg="新密码不能与旧密码相同")
    db = get_db_connection()
    try:
        if not user_exists(db, userid):
            return ApiResponse.error(msg="用户不存在")
        else:
            change_password(db, userid, new_password)
            new_token = generate_jwt(get_user_by_username(db, userid)[0], get_user_by_username(db, userid)[1])
            return ApiResponse.success(data={"token": new_token}, msg="密码修改成功")
    except Exception as e:
        return ApiResponse.error(msg=f"密码修改失败: {str(e)}")
    finally:
        db.close()

# 新增：获取用户信息
def get_user_profile(user_id):
    db = get_db_connection()

    try:
        cursor = db.cursor()
        
        # 检查表有哪些列
        cursor.execute("PRAGMA table_info(users)")
        cols = [c[1] for c in cursor.fetchall()]
        
        # 构建查询语句
        select_cols = ["id", "username", "telephone", "avatar", "ip_address"]
        intro_col = "introduction" if "introduction" in cols else "bio"
        select_cols.append(intro_col)
        
        # 添加新字段
        if "school" in cols:
            select_cols.append("school")
        if "grade" in cols:
            select_cols.append("grade")
        if "role" in cols:
            select_cols.append("role")
        if "like_count" in cols:
            select_cols.append("like_count")
        if "follower_count" in cols:
            select_cols.append("follower_count")
        if "following_count" in cols:
            select_cols.append("following_count")
        if "view_count" in cols:
            select_cols.append("view_count")
        if "study_hours" in cols:
            select_cols.append("study_hours")
        if "question_count" in cols:
            select_cols.append("question_count")
        if "wrong_count" in cols:
            select_cols.append("wrong_count")
        
        cursor.execute(
            f"SELECT {', '.join(select_cols)} FROM users WHERE id = ?",
            (user_id,)
        )

        user = cursor.fetchone()

        if not user:
            return ApiResponse.error(msg="用户不存在")

        data = {
            "id": user[0],
            "username": user[1],
            "telephone": user[2],
            "avatar": user[3] if user[3] else None,
            "ip_address": user[4] if user[4] else None,
            "introduction": user[5] if user[5] else None
        }
        
        # 添加可选字段
        idx = 6
        if "school" in cols:
            data["school"] = user[idx] if user[idx] else None
            idx += 1
        if "grade" in cols:
            data["grade"] = user[idx] if user[idx] else None
            idx += 1
        if "role" in cols:
            data["role"] = user[idx] if user[idx] else "学生"
            idx += 1
        if "like_count" in cols:
            data["like_count"] = user[idx] if user[idx] else 0
            idx += 1
        if "follower_count" in cols:
            data["follower_count"] = user[idx] if user[idx] else 0
            idx += 1
        if "following_count" in cols:
            data["following_count"] = user[idx] if user[idx] else 0
            idx += 1
        if "view_count" in cols:
            data["view_count"] = user[idx] if user[idx] else 0
            idx += 1
        if "study_hours" in cols:
            data["study_hours"] = user[idx] if user[idx] else 0.0
            idx += 1
        if "question_count" in cols:
            data["question_count"] = user[idx] if user[idx] else 0
            idx += 1
        if "wrong_count" in cols:
            data["wrong_count"] = user[idx] if user[idx] else 0

        return ApiResponse.success(data=data, msg="获取成功")

    except Exception as e:
        return ApiResponse.error(msg=f"获取用户信息失败: {str(e)}")

    finally:
        db.close()

# 更新头像
def update_user_avatar(user_id, avatar_data):
    if not avatar_data:
        return ApiResponse.error(msg="头像数据不能为空")
    
    if not avatar_data.startswith('data:image/'):
        return ApiResponse.error(msg="无效的头像数据格式")
    
    db = get_db_connection()
    try:
        cursor = db.cursor()
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            return ApiResponse.error(msg="用户不存在")
        
        success = update_avatar(db, user_id, avatar_data)
        if success:
            return ApiResponse.success(data={"avatar": avatar_data}, msg="头像更新成功")
        else:
            return ApiResponse.error(msg="头像更新失败")
    except Exception as e:
        return ApiResponse.error(msg=f"头像更新失败: {str(e)}")
    finally:
        db.close()

# 修改用户名
def update_user_username(user_id, new_username):
    if not new_username:
        return ApiResponse.error(msg="用户名不能为空")
    
    if len(new_username) < 2 or len(new_username) > 20:
        return ApiResponse.error(msg="用户名长度必须在2到20个字符之间")
    
    db = get_db_connection()
    try:
        if user_exists(db, new_username):
            return ApiResponse.error(msg="用户名已存在")
        
        cursor = db.cursor()
        cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        current_user = cursor.fetchone()
        if not current_user:
            return ApiResponse.error(msg="用户不存在")
        
        success = update_username(db, user_id, new_username)
        if success:
            new_token = generate_jwt(user_id, new_username)
            return ApiResponse.success(data={"token": new_token, "username": new_username}, msg="用户名修改成功")
        else:
            return ApiResponse.error(msg="修改失败")
    except Exception as e:
        return ApiResponse.error(msg=f"修改用户名失败: {str(e)}")
    finally:
        db.close()

# 更新IP地址
def update_user_ip_address(user_id, ip_address):
    db = get_db_connection()
    try:
        cursor = db.cursor()
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            return ApiResponse.error(msg="用户不存在")
        
        cursor.execute("UPDATE users SET ip_address = ? WHERE id = ?", (ip_address, user_id))
        db.commit()
        
        return ApiResponse.success(msg="IP地址更新成功")
    except Exception as e:
        return ApiResponse.error(msg=f"IP地址更新失败: {str(e)}")
    finally:
        db.close()

# 更新个人简介
def update_user_introduction(user_id, introduction):
    db = get_db_connection()
    try:
        cursor = db.cursor()
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            return ApiResponse.error(msg="用户不存在")
        
        # 先检查用哪个列
        cursor.execute("PRAGMA table_info(users)")
        cols = [c[1] for c in cursor.fetchall()]
        intro_col = "introduction" if "introduction" in cols else "bio"
        
        # 直接更新，而不是通过model函数
        cursor.execute(f"UPDATE users SET {intro_col} = ? WHERE id = ?", (introduction, user_id))
        db.commit()
        
        return ApiResponse.success(data={"introduction": introduction}, msg="个人简介更新成功")
    except Exception as e:
        return ApiResponse.error(msg=f"更新个人简介失败: {str(e)}")
    finally:
        db.close()

# 获取用户统计数据
def get_user_statistics(user_id):
    db = get_db_connection()
    try:
        stats = get_user_stats(db, user_id)
        if stats:
            return ApiResponse.success(data=stats)
        else:
            return ApiResponse.error(msg="用户不存在")
    except Exception as e:
        return ApiResponse.error(msg=f"获取用户统计数据失败: {str(e)}")
    finally:
        db.close()

# 关注用户
def follow_user_service(follower_id, following_id):
    if follower_id == following_id:
        return ApiResponse.error(msg="不能关注自己")
    
    db = get_db_connection()
    try:
        cursor = db.cursor()
        cursor.execute("SELECT id FROM users WHERE id = ?", (following_id,))
        user = cursor.fetchone()
        if not user:
            return ApiResponse.error(msg="用户不存在")
        
        if is_following(db, follower_id, following_id):
            return ApiResponse.error(msg="已关注该用户")
        
        success = follow_user(db, follower_id, following_id)
        if success:
            increment_follower_count(db, following_id)
            increment_following_count(db, follower_id)
            return ApiResponse.success(msg="关注成功")
        else:
            return ApiResponse.error(msg="关注失败")
    except Exception as e:
        return ApiResponse.error(msg=f"关注失败: {str(e)}")
    finally:
        db.close()

# 取消关注
def unfollow_user_service(follower_id, following_id):
    if follower_id == following_id:
        return ApiResponse.error(msg="不能取消关注自己")
    
    db = get_db_connection()
    try:
        if not is_following(db, follower_id, following_id):
            return ApiResponse.error(msg="未关注该用户")
        
        success = unfollow_user(db, follower_id, following_id)
        if success:
            decrement_follower_count(db, following_id)
            decrement_following_count(db, follower_id)
            return ApiResponse.success(msg="取消关注成功")
        else:
            return ApiResponse.error(msg="取消关注失败")
    except Exception as e:
        return ApiResponse.error(msg=f"取消关注失败: {str(e)}")
    finally:
        db.close()

# 检查关注状态
def check_follow_status(follower_id, following_id):
    db = get_db_connection()
    try:
        followed = is_following(db, follower_id, following_id)
        return ApiResponse.success(data={"followed": followed})
    except Exception as e:
        return ApiResponse.error(msg=f"查询失败: {str(e)}")
    finally:
        db.close()

# 增加主页浏览量
def increment_profile_view(user_id):
    db = get_db_connection()
    try:
        success = increment_view_count(db, user_id)
        if success:
            return ApiResponse.success(msg="浏览量增加成功")
        else:
            return ApiResponse.error(msg="用户不存在")
    except Exception as e:
        return ApiResponse.error(msg=f"增加浏览量失败: {str(e)}")
    finally:
        db.close()

# 获取粉丝列表
def get_user_followers(user_id):
    db = get_db_connection()
    try:
        followers = get_followers(db, user_id)
        data = []
        for f in followers:
            data.append({
                "user_id": f[0],
                "username": f[1],
                "avatar": f[2] if f[2] else None
            })
        return ApiResponse.success(data=data)
    except Exception as e:
        return ApiResponse.error(msg=f"获取粉丝列表失败: {str(e)}")
    finally:
        db.close()

# 获取关注列表
def get_user_following(user_id):
    db = get_db_connection()
    try:
        following = get_following(db, user_id)
        data = []
        for f in following:
            data.append({
                "user_id": f[0],
                "username": f[1],
                "avatar": f[2] if f[2] else None
            })
        return ApiResponse.success(data=data)
    except Exception as e:
        return ApiResponse.error(msg=f"获取关注列表失败: {str(e)}")
    finally:
        db.close()

# 获取点赞用户列表
def get_user_likers(user_id):
    db = get_db_connection()
    try:
        likers = get_post_likers(db, user_id)
        data = []
        for l in likers:
            data.append({
                "user_id": l[0],
                "username": l[1],
                "avatar": l[2] if l[2] else None
            })
        return ApiResponse.success(data=data)
    except Exception as e:
        return ApiResponse.error(msg=f"获取点赞用户列表失败: {str(e)}")
    finally:
        db.close()

# 更新用户信息
def update_user_info(user_id, school=None, grade=None, role=None, introduction=None, ip_address=None):
    db = get_db_connection()
    try:
        cursor = db.cursor()
        cursor.execute("SELECT id FROM users WHERE id = ?", (user_id,))
        user = cursor.fetchone()
        if not user:
            return ApiResponse.error(msg="用户不存在")
        
        # 检查表有哪些列
        cursor.execute("PRAGMA table_info(users)")
        cols = [c[1] for c in cursor.fetchall()]
        
        # 构建更新语句
        updates = []
        params = []
        
        if school is not None and "school" in cols:
            updates.append("school = ?")
            params.append(school)
        if grade is not None and "grade" in cols:
            updates.append("grade = ?")
            params.append(grade)
        if role is not None and "role" in cols:
            updates.append("role = ?")
            params.append(role)
        if introduction is not None:
            intro_col = "introduction" if "introduction" in cols else "bio"
            updates.append(f"{intro_col} = ?")
            params.append(introduction)
        if ip_address is not None and "ip_address" in cols:
            updates.append("ip_address = ?")
            params.append(ip_address)
        
        if not updates:
            return ApiResponse.error(msg="没有要更新的字段")
        
        params.append(user_id)
        cursor.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", params)
        db.commit()
        
        return ApiResponse.success(msg="用户信息更新成功")
    except Exception as e:
        return ApiResponse.error(msg=f"更新用户信息失败: {str(e)}")
    finally:
        db.close()