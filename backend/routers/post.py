from service.post import create_post, get_posts_by_tag
from fastapi import FastAPI, File, UploadFile, APIRouter,Header
import uuid
from model.request import CreatePostRequest
from utils.response import ApiResponse

router = APIRouter()

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

@router.post("/create_post")
def create_post_api(
    req: CreatePostRequest,
    token: str = Header(...)
):
    return create_post(token, req.content, req.image_urls, req.tag)

@router.get("/posts")
def get_posts_by_tag_api(tag: str = "", page: int = 1, page_size: int = 10):
    return get_posts_by_tag(tag, page, page_size)