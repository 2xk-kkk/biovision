from fastapi import FastAPI, File, UploadFile, APIRouter, Header, Query, HTTPException
import uuid
import os
from model.request import CreatePostRequest
from service.post import (
    create_post,
    get_all_posts,
    get_posts_by_tag,
    get_post_detail,
    update_post_api,
    delete_post_api,
    like_post,
    collect_post,
    share_post,
    create_comment,
    get_post_comments_service, 
    get_user_posts_service     
)

router = APIRouter()

# 上传图片
@router.post("/upload_image")
def upload_image(file: UploadFile = File(...)):
    ext = file.filename.split(".")[-1]
    new_filename = f"{uuid.uuid4()}.{ext}"
    save_path = f"uploads/{new_filename}"
    with open(save_path, "wb") as f:
        f.write(file.file.read())
    image_url = f"/uploads/{new_filename}"
    print("图片上传成功，访问URL:", image_url)
    return {"image_url": image_url}

# 发布帖子
@router.post("/create_post")
def create_post_api(
    req: CreatePostRequest,
    token: str = Header(...)
):
    return create_post(token, req.content, req.image_urls, req.tag)

# 获取帖子列表（全部 / 按标签）
@router.get("/posts")
def get_posts(
    tag: str = Query("", description="按标签筛选，留空则返回所有帖子"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    if tag:
        return get_posts_by_tag(tag, page, page_size)
    return get_all_posts(page, page_size)

# 浏览量 
@router.get("/post/{post_id}")
def get_post_detail_api(post_id: int):
    return get_post_detail(post_id)

# 发布评论
@router.post("/post/{post_id}/comment")
def create_comment_api(
    post_id: int,
    content: str,
    token: str = Header(...)
):
    return create_comment(token, post_id, content)

# 获取帖子的所有评论 
@router.get("/post/{post_id}/comments")
def get_post_comments_api(post_id: int):
    return get_post_comments_service(post_id)  # 这里也改对

# 获取某个用户发布的所有帖子 
@router.get("/user/{user_id}/posts")
def get_user_posts_api(
    user_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1)
):
    return get_user_posts_service(user_id, page, page_size)  # 这里也改对

# 编辑帖子
@router.put("/post/{post_id}")
def update_post(
    post_id: int,
    req: CreatePostRequest,
    token: str = Header(...)
):
    return update_post_api(token, post_id, req.content, req.image_urls, req.tag)

# 删除帖子
@router.delete("/post/{post_id}")
def delete_post(
    post_id: int,
    token: str = Header(...)
):
    return delete_post_api(token, post_id)

# 点赞
@router.post("/post/{post_id}/like")
def like_post_api(
    post_id: int,
    token: str = Header(...)
):
    return like_post(token, post_id)

# 收藏
@router.post("/post/{post_id}/collect")
def collect_post_api(
    post_id: int,
    token: str = Header(...)
):
    return collect_post(token, post_id)

# 分享
@router.post("/post/{post_id}/share")
def share_post_api(post_id: int):
    return share_post(post_id)