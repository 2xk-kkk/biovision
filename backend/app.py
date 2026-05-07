# app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import user, post
from utils.response import ApiResponse
from database.db import init_db
import os
from fastapi.staticfiles import StaticFiles

init_db()

app = FastAPI(
    title="论坛 API",
    description="一个简单的论坛后端",
    version="1.0.0"
)

#配置 CORS（允许前端跨域调用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

#配置静态文件目录（用于上传图片）
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

#注册路由
app.include_router(user.router, prefix="/api", tags=["用户"])
app.include_router(post.router, prefix="/api", tags=["发帖"])

#根路径
@app.get("/")
def root():
    return {"message": "论坛 API 服务正常运行"}

@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )