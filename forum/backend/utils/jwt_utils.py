#jwt 生成与验证
import jwt
import datetime

secret_key = 's7f9j2k3l4m5n6b7v8c9x0z1a2s3'  

#生成token
def generate_jwt(user_id, user_name):
    payload = {
        'user_id': user_id,
        'user_name': user_name,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7), # 设置过期时间为7天
        'iat': datetime.datetime.utcnow()# 设置签发时间   
    }
    token = jwt.encode(payload, secret_key, algorithm='HS256')
    return token

#验证token
def verify_jwt(token):
    try:
        payload = jwt.decode(token, secret_key, algorithms=['HS256'])
        return {'msg':payload,"success": True}
    except jwt.ExpiredSignatureError:
        return {'msg':'token已过期',"success": False} # token过期
    except jwt.InvalidTokenError:
        return {'msg':'token无效',"success": False}  # token无效