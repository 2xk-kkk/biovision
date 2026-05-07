#用户功能业务逻辑
from utils.crypto import verify_password
from model.user import register, get_user_by_username, delete_user, change_password, user_exists 
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
    if old_password!= new_password:
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