from service.post import create_post, get_post, delete_post, update_post
from fastapi import FastAPI, File, UploadFile, APIRouter,Header
import uuid
from model.request import CreatePostRequest
from utils.response import ApiResponse
from service.post import create_post as create_post_service

router = APIRouter()

@router.post("/upload_image")
def upload_image(file: UploadFile = File(...)):
    # 1. 获取文件后缀
    ext = file.filename.split(".")[-1]
    # 2. 生成唯一文件名
    new_filename = f"{uuid.uuid4()}.{ext}"
    # 3. 保存到服务器
    save_path = f"uploads/{new_filename}"
    with open(save_path, "wb") as f:
        f.write(file.file.read())
    # 4. 生成访问URL
    image_url = f"/uploads/{new_filename}"
    
    # 5. 返回URL给前端
    return {"image_url": image_url}

@router.post("/create_post")
def create_post_api(
    req: CreatePostRequest,
    token: str = Header(...)
):
    return create_post_service(token, req.content, req.image_urls)