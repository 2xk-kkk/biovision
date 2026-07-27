#密码加密和解密
import hashlib

#密码加密
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

#密码验证
def verify_password(password, hashed):
    return hash_password(password) == hashed