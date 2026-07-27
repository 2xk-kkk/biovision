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
UPLOAD_DIR = os.path.join(BASE_DIR, "uploads")

# 创建目录
os.makedirs(UPLOAD_DIR, exist_ok=True)

# 挂载静态文件服务
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

# 挂载前端静态文件目录
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend")
app.mount("/static", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

#注册路由
app.include_router(user.router, prefix="/api", tags=["用户"])
app.include_router(post.router, prefix="/api", tags=["发帖"])
app.include_router(chart.router, prefix="/api", tags=["统计"])
app.include_router(exam.router, prefix="/api", tags=["试卷"])
app.include_router(question.router, prefix="/api", tags=["题目"])

#根路径 - 提供前端页面
@app.get("/")
def root():
    from fastapi.responses import FileResponse
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    return FileResponse(index_path)

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