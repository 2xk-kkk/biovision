#帖子相关业务逻辑
from utils.jwt_utils import verify_jwt
from utils.response import ApiResponse
from database.db import get_db_connection
from model.post import create_post, create_post_image 

def create_post(token, content, image_urls):
    db= get_db_connection()
    payload = verify_jwt(token)
    if not payload:
        return ApiResponse.error(msg="请先登录")
    user_id = payload.get("user_id")
    try:
        post_id = create_post(db, user_id, content)
        for index, image_url in enumerate(image_urls):
            create_post_image(db, post_id, image_url, index)
        return ApiResponse.success(data={"post_id": post_id}, msg="帖子创建成功")
    except Exception as e:
        return ApiResponse.error(msg=f"发帖失败: {str(e)}")
    finally:
        db.close()