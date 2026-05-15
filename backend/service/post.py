from utils.jwt_utils import verify_jwt
from utils.response import ApiResponse
from database.db import get_db_connection
from model.post import create_post as create_post_db, create_post_image, get_posts_by_tag_db, get_post_images, get_posts, get_post_images_by_post_ids

def create_post(token, content, image_urls, tag):
    print(f"[DEBUG] create_post called with token={token[:20] if token else 'None'}, content={content[:50] if token else 'None'}, image_urls={image_urls}, tag={tag}")
    print(f"[DEBUG] image_urls type: {type(image_urls)}, value: {image_urls}")
    
    db = get_db_connection()
    payload = verify_jwt(token)
    
    if not payload.get("success"):
        return ApiResponse.error(msg="请先登录")
    
    user_id = payload.get("msg").get("user_id")
    if user_id is None:
        return ApiResponse.error(msg="用户ID无效")
    
    user_id = int(user_id)
    
    try:
        post_id = create_post_db(db, user_id, content, tag)

        if image_urls:
            valid_image_urls = []
            if isinstance(image_urls, list):
                valid_image_urls = image_urls
            elif image_urls and isinstance(image_urls, str):
                valid_image_urls = [image_urls]
            
            for index, image_url in enumerate(valid_image_urls):
                if image_url and str(image_url).strip():
                    create_post_image(db, post_id, str(image_url).strip(), index)
        
        db.commit()
        return ApiResponse.success(data={"post_id": post_id}, msg="帖子创建成功")
    except Exception as e:
        print(f"[DEBUG] Error: {type(e).__name__}: {str(e)}")
        import traceback
        traceback.print_exc()
        return ApiResponse.error(msg=f"发帖失败: {str(e)}")
    finally:
        db.close()

def get_posts_by_tag(tag, page=1, page_size=10):
    db = get_db_connection()
    try:
        # ==============================================
        # 🔥 修复：正确统计标签数量
        # ==============================================
        cursor = db.cursor()
        if tag:
            cursor.execute("SELECT COUNT(*) FROM posts WHERE tag = ?", (tag,))
        else:
            cursor.execute("SELECT COUNT(*) FROM posts")
        total_count = cursor.fetchone()[0]

        post_data = get_posts_by_tag_db(db, tag, page, page_size)

        if not post_data:
            return ApiResponse.success(data={
                "posts": [],
                "total": total_count,
                "page": page,
                "page_size": page_size
            }, msg="没有找到相关帖子")
        
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
        
        return ApiResponse.success(data={
            "posts": posts_list,
            "total": total_count,
            "page": page,
            "page_size": page_size
        }, msg="获取帖子成功")
        
    except Exception as e:
        print(f"[DEBUG] 获取标签失败: {e}")
        return ApiResponse.error(msg=f"获取帖子失败: {str(e)}")
    finally:
        db.close()

def get_all_posts(page=1, page_size=20):
    db = get_db_connection()
    try:
        posts_data = get_posts(db, page, page_size)

        cursor = db.cursor()
        cursor.execute("SELECT COUNT(*) FROM posts")
        total_count = cursor.fetchone()[0]

        if not posts_data:
            return ApiResponse.success(data={
                "posts": [],
                "total": total_count,
                "page": page,
                "page_size": page_size
            }, msg="暂无帖子")

        posts_list = []
        post_ids = []
        for row in posts_data:
            post_id = row[0]
            post_ids.append(post_id)
            posts_list.append({
                "post_id": post_id,
                "user_id": row[1],
                "username": row[2],
                "content": row[3],
                "tag": row[4],
                "create_at": row[5],
                "images": []
            })

        if post_ids:
            images = get_post_images_by_post_ids(db, post_ids)
            for post in posts_list:
                post["images"] = images.get(post["post_id"], [])

        return ApiResponse.success(data={
            "posts": posts_list,
            "total": total_count,
            "page": page,
            "page_size": page_size
        }, msg="获取成功")
    finally:
        db.close()