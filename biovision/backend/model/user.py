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