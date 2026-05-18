from utils.jwt_utils import verify_jwt
from utils.response import ApiResponse
from database.db import get_db_connection
from model.post import (
    create_post as create_post_db,
    create_post_image,
    get_posts_by_tag_db,
    get_post_images,
    get_posts,
    get_post_images_by_post_ids,
    #新增
    get_post_detail as get_post_detail_db,
    add_view_count,
    update_post,
    delete_post,
    get_post_user_id,
    toggle_like,
    is_liked,
    toggle_collect,
    is_collected,
    add_share_count,
    create_comment,
    get_post_comments,
    get_user_posts,
    delete_post_images
)

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

# 1. 获取帖子详情 + 浏览量+1
def get_post_detail(post_id):
    db = get_db_connection()
    try:
        add_view_count(db, post_id)
        post = get_post_detail_db(db, post_id)
        if not post:
            return ApiResponse.error(msg="帖子不存在")
        
        images = get_post_images_by_post_ids(db, [post_id])
        return ApiResponse.success(data={
            "post_id": post[0],
            "user_id": post[1],
            "username": post[2],
            "content": post[3],
            "tag": post[4],
            "create_at": post[5],
            "view_count": post[6],
            "like_count": post[7],
            "collect_count": post[8],
            "images": images.get(post_id, [])
        })
    finally:
        db.close()

# 2. 发布评论
def create_comment(token, post_id, content):
    db = get_db_connection()
    payload = verify_jwt(token)
    if not payload["success"]:
        return ApiResponse.error(msg="请先登录")
    user_id = int(payload["msg"]["user_id"])
    
    try:
        cid = create_comment(db, post_id, user_id, content)
        return ApiResponse.success(data={"comment_id": cid}, msg="评论成功")
    except:
        return ApiResponse.error(msg="评论失败")
    finally:
        db.close()

# 3. 获取帖子评论
def get_post_comments_service(post_id):
    db = get_db_connection()
    try:
        comments = get_post_comments(db, post_id)
        data = []
        for c in comments:
            data.append({
                "id": c[0],
                "user_id": c[1],
                "username": c[2],
                "content": c[3],
                "create_at": c[4],
                "like_count": c[5]
            })
        return ApiResponse.success(data=data)
    finally:
        db.close()

# 4. 获取用户发布的帖子
def get_user_posts_service(user_id, page=1, page_size=10):
    db = get_db_connection()
    try:
        posts = get_user_posts(db, user_id, page, page_size)
        post_ids = [p[0] for p in posts]
        images = get_post_images_by_post_ids(db, post_ids)
        res = []
        for p in posts:
            res.append({
                "post_id": p[0],
                "user_id": p[1],
                "username": p[2],
                "content": p[3],
                "tag": p[4],
                "create_at": p[5],
                "view_count": p[6],
                "like_count": p[7],
                "collect_count": p[8],
                "images": images.get(p[0], [])
            })
        return ApiResponse.success(data=res)
    finally:
        db.close()

# 5. 编辑帖子
def update_post_api(token, post_id, content, image_urls, tag):
    db = get_db_connection()
    payload = verify_jwt(token)
    if not payload["success"]:
        return ApiResponse.error(msg="请先登录")
    user_id = int(payload["msg"]["user_id"])
    post_user_id = get_post_user_id(db, post_id)
    
    if post_user_id != user_id:
        return ApiResponse.error(msg="无权限")
    
    try:
        update_post(db, post_id, content, tag)
        delete_post_images(db, post_id)
        if image_urls:
            for i, url in enumerate(image_urls):
                create_post_image(db, post_id, url, i)
        db.commit()
        return ApiResponse.success(msg="修改成功")
    except:
        return ApiResponse.error(msg="修改失败")
    finally:
        db.close()

# 6. 删除帖子
def delete_post_api(token, post_id):
    db = get_db_connection()
    payload = verify_jwt(token)
    if not payload["success"]:
        return ApiResponse.error(msg="请先登录")
    user_id = int(payload["msg"]["user_id"])
    post_user_id = get_post_user_id(db, post_id)
    
    if post_user_id != user_id:
        return ApiResponse.error(msg="无权限")
    
    delete_post(db, post_id)
    db.close()
    return ApiResponse.success(msg="删除成功")

# 7. 点赞
def like_post(token, post_id):
    db = get_db_connection()
    payload = verify_jwt(token)
    if not payload["success"]:
        return ApiResponse.error(msg="请先登录")
    user_id = int(payload["msg"]["user_id"])
    
    status = toggle_like(db, user_id, post_id)
    count = get_post_detail(post_id)[7]
    db.close()
    return ApiResponse.success(data={"liked": status, "like_count": count})

# 8. 收藏
def collect_post(token, post_id):
    db = get_db_connection()
    payload = verify_jwt(token)
    if not payload["success"]:
        return ApiResponse.error(msg="请先登录")
    user_id = int(payload["msg"]["user_id"])
    
    status = toggle_collect(db, user_id, post_id)
    count = get_post_detail(db, post_id)[8]
    db.close()
    return ApiResponse.success(data={"collected": status, "collect_count": count})

# 9. 分享
def share_post(post_id):
    db = get_db_connection()
    add_share_count(db, post_id)
    db.close()
    return ApiResponse.success(msg="分享成功")