from utils.jwt_utils import verify_jwt
from utils.response import ApiResponse
from database.db import get_db_connection
from model.post import create_post, create_post_image, get_posts_by_tag_db, get_post_images

def create_post(token, content, image_urls, tag):
    db = get_db_connection()
    payload = verify_jwt(token)
    if not payload.get("success"):
        return ApiResponse.error(msg="请先登录")
    user_id = payload.get("msg").get("user_id")
    try:
        post_id = create_post(db, user_id, content, tag)
        for index, image_url in enumerate(image_urls):
            create_post_image(db, post_id, image_url, index)
        return ApiResponse.success(data={"post_id": post_id}, msg="帖子创建成功")
    except Exception as e:
        return ApiResponse.error(msg=f"发帖失败: {str(e)}")
    finally:
        db.close()

def get_posts_by_tag(tag, page=1, page_size=10):
    db = get_db_connection()
    try:
        post_data = get_posts_by_tag_db(db, tag, page, page_size)
        
        if not post_data:
            return ApiResponse.success(data={"posts": []}, msg="没有找到相关帖子")
        
        posts_list = []
        post_ids = []
        for row in post_data:
            post_id = row[0]
            post_ids.append(post_id)
            posts_list.append({
                "post_id": post_id,
                "user_id": row[1],
                "username": row[2],
                "content": row[3],
                "create_at": row[4],
                "tag": row[5],
                "images": [] 
            })
        
        if post_ids:
            images = get_post_images(db, post_ids)
            for post in posts_list:
                 post["images"] = images.get(post["post_id"], [])
        
        return ApiResponse.success(data={"posts": posts_list}, msg="获取帖子成功")
        
    except Exception as e:
        return ApiResponse.error(msg=f"获取帖子失败: {str(e)}")
    finally:
        db.close()