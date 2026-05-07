# app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import user
from utils.response import ApiResponse
from database.db import init_db
import uuid
import os
from fastapi.staticfiles import StaticFiles

init_db()

# 1. 创建 FastAPI 应用
app = FastAPI(
    title="论坛 API",
    description="一个简单的论坛后端",
    version="1.0.0"
)

# 2. 配置 CORS（允许前端跨域调用）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 配置静态文件目录（用于上传图片）
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# 3. 注册路由
app.include_router(user.router, prefix="/api", tags=["用户"])
app.include_router(user.router, prefix="/api/posts", tags=["发帖"])

# 4. 根路径
@app.get("/")
def root():
    return {"message": "论坛 API 服务正常运行"}

# 5. 健康检查
@app.get("/health")
def health():
    return {"status": "ok"}

# 6. 启动命令（直接运行此文件时执行）
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="127.0.0.1",
        port=8000,
        reload=True  # 开发模式，代码改变自动重启
    )