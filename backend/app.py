# app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import user, post, exam, question
from utils.response import ApiResponse
from database.db import init_db
import os
from fastapi.staticfiles import StaticFiles
from service.chart import get_forum_stats
from routers import chart  

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
# 使用绝对路径确保所有用户访问同一目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_DIR = os.path.dirname(BASE_DIR)  # 项目根目录
UPLOAD_DIR = os.path.join(PROJECT_DIR, "uploads")
BACKEND_UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")  # 旧的上传目录

# 创建目录
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(BACKEND_UPLOAD_DIR, exist_ok=True)

# 尝试将旧目录中的文件复制到新目录（包括子目录）
import shutil
for item in os.listdir(BACKEND_UPLOAD_DIR):
    src = os.path.join(BACKEND_UPLOAD_DIR, item)
    dst = os.path.join(UPLOAD_DIR, item)
    if os.path.isfile(src) and not os.path.exists(dst):
        shutil.copy2(src, dst)
        print(f"复制文件: {item}")
    elif os.path.isdir(src) and not os.path.exists(dst):
        shutil.copytree(src, dst)
        print(f"复制目录: {item}")

# 挂载静态文件服务
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

#注册路由
app.include_router(user.router, prefix="/api", tags=["用户"])
app.include_router(post.router, prefix="/api", tags=["发帖"])
app.include_router(chart.router, prefix="/api", tags=["统计"])
app.include_router(exam.router, prefix="/api", tags=["试卷"])
app.include_router(question.router, prefix="/api", tags=["题目"])

#根路径
@app.get("/")
def root():
    return {"message": "论坛 API 服务正常运行"}

@app.get("/health")
def health():
    return {"status": "ok"}

# 论坛统计接口
@app.get("/api/stats")
def stats():
    return get_forum_stats()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True
        
    )