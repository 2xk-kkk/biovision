from utils.jwt_utils import verify_jwt
from utils.response import ApiResponse
from database.db import get_db_connection
from model.post import (
    create_post as create_post_db,
    create_post_image,
    get_posts_by_tag_db,
    get_post_images,
    get_posts,
    get_posts_with_counts,
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
    create_comment as create_comment_db,
    get_post_comments,
    get_user_posts,
    delete_post_images,
    get_user_collect_posts,
    get_user_liked_posts,
    toggle_comment_like
)
from model.user import get_user_stats

def create_post(token, content, image_urls, tag, tags=None, file_urls=None):
    print(f"[DEBUG] create_post called with token={token[:20] if token else 'None'}, content={content[:50] if token else 'None'}, image_urls={image_urls}, tag={tag}, tags={tags}, file_urls={file_urls}")
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
        post_id = create_post_db(db, user_id, content, tag, tags)

        # 处理图片URL
        if image_urls:
            valid_image_urls = []
            if isinstance(image_urls, list):
                valid_image_urls = image_urls
            elif image_urls and isinstance(image_urls, str):
                valid_image_urls = [image_urls]
            
            for index, image_url in enumerate(valid_image_urls):
                if image_url and str(image_url).strip():
                    create_post_image(db, post_id, str(image_url).strip(), index)
        
        # 处理文件URL（包括Word、Excel、PDF等）
        if file_urls:
            valid_file_urls = []
            if isinstance(file_urls, list):
                valid_file_urls = file_urls
            elif file_urls and isinstance(file_urls, str):
                valid_file_urls = [file_urls]
            
            # 从现有的图片数量开始编号
            image_count = len([url for url in (image_urls or []) if url])
            for index, file_url in enumerate(valid_file_urls):
                if file_url and str(file_url).strip():
                    create_post_image(db, post_id, str(file_url).strip(), image_count + index)
        
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
            cursor.execute("SELECT COUNT(*) FROM comments WHERE post_id = ?", (post_id,))
            comment_count = cursor.fetchone()[0]
            posts_list.append({
                "post_id": post_id,
                "user_id": row[1],
                "username": row[2],
                "content": row[3],
                "create_at": row[4],
                "tag": row[5],
                "comment_count": comment_count,
                "like_count": row[6] if len(row) > 6 else 0,
                "view_count": row[7] if len(row) > 7 else 0,
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
        posts_data = get_posts_with_counts(db, page, page_size)

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
            # 解析标签字符串为列表
            tags_str = row[11] if len(row) > 11 else None
            tags = tags_str.split(",") if tags_str else []
            posts_list.append({
                "post_id": post_id,
                "user_id": row[1],
                "username": row[2],
                "avatar": row[3] if len(row) > 3 else None,
                "content": row[4] if len(row) > 4 else '',
                "tag": row[5] if len(row) > 5 else '',
                "create_at": row[6] if len(row) > 6 else '',
                "comment_count": row[7] if len(row) > 7 else 0,
                "like_count": row[8] if len(row) > 8 else 0,
                "view_count": row[9] if len(row) > 9 else 0,
                "collect_count": row[10] if len(row) > 10 else 0,
                "tags": tags,
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
        
        comments = get_post_comments(db, post_id)
        comment_count = len(comments)
        
        # 获取所有附件（图片和文件）
        all_attachments = get_post_images_by_post_ids(db, [post_id]).get(post_id, [])
        
        # 区分图片和文件
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg']
        images = []
        files = []
        for attachment in all_attachments:
            lower_url = attachment.lower()
            is_image = any(lower_url.endswith(ext) for ext in image_extensions)
            if is_image:
                images.append(attachment)
            else:
                files.append(attachment)
        
        return ApiResponse.success(data={
            "post_id": post[0],
            "user_id": post[1],
            "username": post[2],
            "content": post[3],
            "tag": post[4],
            "create_at": post[5],
            "view_count": post[6] if len(post) > 6 else 0,
            "like_count": post[7] if len(post) > 7 else 0,
            "collect_count": post[8] if len(post) > 8 else 0,
            "comment_count": comment_count,
            "images": images,
            "files": files,
            "avatar": post[10] if len(post) > 10 else None
        })
    finally:
        db.close()

# 2. 发布评论
def create_comment(token, post_id, content, parent_id=None):
    db = get_db_connection()
    payload = verify_jwt(token)
    if not payload["success"]:
        return ApiResponse.error(msg="请先登录")
    user_id = int(payload["msg"]["user_id"])
    
    try:
        cid = create_comment_db(db, post_id, user_id, content, parent_id)
        return ApiResponse.success(data={"comment_id": cid}, msg="评论成功")
    except Exception as e:
        print(f"[DEBUG] 创建评论失败: {e}")
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
                "avatar": c[3] if c[3] else None,
                "content": c[4],
                "create_at": c[5],
                "like_count": c[6],
                "parent_id": c[7] if len(c) > 7 else None
            })
        return ApiResponse.success(data=data)
    finally:
        db.close()

# 4. 评论点赞
def like_comment(token, comment_id):
    db = get_db_connection()
    payload = verify_jwt(token)
    if not payload["success"]:
        db.close()
        return ApiResponse.error(msg="请先登录")
    user_id = int(payload["msg"]["user_id"])
    
    try:
        like_count, liked = toggle_comment_like(db, user_id, comment_id)
        if like_count is None:
            return ApiResponse.error(msg="评论不存在")
        return ApiResponse.success(data={"liked": liked, "like_count": like_count})
    except Exception as e:
        print(f"[DEBUG] 评论点赞失败: {e}")
        return ApiResponse.error(msg="点赞失败")
    finally:
        db.close()

# 5. 获取用户发布的帖子
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
                "avatar": p[3] if len(p) > 3 else None,
                "content": p[4] if len(p) > 4 else '',
                "tag": p[5] if len(p) > 5 else '',
                "create_at": p[6] if len(p) > 6 else '',
                "view_count": p[7] if len(p) > 7 else 0,
                "like_count": p[8] if len(p) > 8 else 0,
                "collect_count": p[9] if len(p) > 9 else 0,
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
    comment_count = len(get_post_comments(db, post_id))
    
    # 获取点赞数
    cursor = db.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM user_interact WHERE post_id=? AND type='like'", (post_id,))
        like_count = cursor.fetchone()[0]
    except:
        like_count = 0
    
    db.close()
    return ApiResponse.success(data={"liked": status, "like_count": like_count, "comment_count": comment_count})

# 8. 收藏
def collect_post(token, post_id):
    db = get_db_connection()
    payload = verify_jwt(token)
    if not payload["success"]:
        return ApiResponse.error(msg="请先登录")
    user_id = int(payload["msg"]["user_id"])
    
    # 收藏/取消收藏
    status = toggle_collect(db, user_id, post_id)

    # 获取最新收藏数
    post = get_post_detail_db(db, post_id)
    count = post[8] if (post and len(post) > 8) else 0
    
    db.close()
    
    # 返回前端需要的格式
    return ApiResponse.success(data={
        "is_collected": status,
        "collect_count": count
    })
# 9. 分享
def share_post(post_id):
    db = get_db_connection()
    add_share_count(db, post_id)
    db.close()
    return ApiResponse.success(msg="分享成功")


# 10. 获取用户统计数据
def get_user_statistics(user_id):
    db = get_db_connection()
    try:
        stats = get_user_stats(db, user_id)
        return ApiResponse.success(data=stats)
    finally:
        db.close()

# 11. 查询是否已收藏 
def is_collected_post(token, post_id):
    db = get_db_connection()
    payload = verify_jwt(token)
    if not payload["success"]:
        return ApiResponse.error(msg="请先登录")
    user_id = int(payload["msg"]["user_id"])
    
    collected = is_collected(db, user_id, post_id)
    db.close()
    return ApiResponse.success(data={"is_collected": collected})

# 12. 获取用户收藏的帖子
def get_user_collect_posts_service(user_id, page=1, page_size=10):
    db = get_db_connection()
    try:
        posts = get_user_collect_posts(db, user_id, page, page_size)
        post_ids = [p[0] for p in posts]
        images = get_post_images_by_post_ids(db, post_ids)
        res = []
        for p in posts:
            res.append({
                "post_id": p[0],
                "user_id": p[1],
                "username": p[2],
                "avatar": p[3] if len(p) > 3 else None,
                "content": p[4] if len(p) > 4 else '',
                "tag": p[5] if len(p) > 5 else '',
                "create_at": p[6] if len(p) > 6 else '',
                "view_count": p[7] if len(p) > 7 else 0,
                "like_count": p[8] if len(p) > 8 else 0,
                "collect_count": p[9] if len(p) > 9 else 0,
                "images": images.get(p[0], [])
            })
        return ApiResponse.success(data=res)
    finally:
        db.close()

# 13. 获取用户点赞的帖子
def get_user_liked_posts_service(user_id, page=1, page_size=10):
    db = get_db_connection()
    try:
        posts = get_user_liked_posts(db, user_id, page, page_size)
        post_ids = [p[0] for p in posts]
        images = get_post_images_by_post_ids(db, post_ids)
        res = []
        for p in posts:
            res.append({
                "post_id": p[0],
                "user_id": p[1],
                "username": p[2],
                "avatar": p[3] if len(p) > 3 else None,
                "content": p[4] if len(p) > 4 else '',
                "tag": p[5] if len(p) > 5 else '',
                "create_at": p[6] if len(p) > 6 else '',
                "view_count": p[7] if len(p) > 7 else 0,
                "like_count": p[8] if len(p) > 8 else 0,
                "collect_count": p[9] if len(p) > 9 else 0,
                "images": images.get(p[0], [])
            })
        return ApiResponse.success(data=res)
    finally:
        db.close()