# app.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import user, post, exam, question, ppt
from utils.response import ApiResponse
from database.db import init_db
import os
from fastapi.staticfiles import StaticFiles
from service.chart import get_forum_stats
from routers import chart, mindmap, pk
from PPT.generator import OUTPUT_DIR as PPT_OUTPUT_DIR, ASSET_DIR as PPT_ASSET_DIR  

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

# 挂载前端静态文件目录（必须在API路由之前，使用root_path避免覆盖API）
FRONTEND_DIR = os.path.join(os.path.dirname(BASE_DIR), "frontend")

#注册路由
app.include_router(user.router, prefix="/api", tags=["用户"])
app.include_router(post.router, prefix="/api", tags=["发帖"])
app.include_router(chart.router, prefix="/api", tags=["统计"])
app.include_router(exam.router, prefix="/api", tags=["试卷"])
app.include_router(question.router, prefix="/api", tags=["题目"])
app.include_router(ppt.router, prefix="/api", tags=["PPT生成"])
app.include_router(mindmap.router, prefix="/api", tags=["思维导图"])
app.include_router(pk.router, prefix="/api", tags=["院校PK"])

# 挂载 PPT 输出文件和资源文件（需要挂载两个路径，因为 HTML 内相对路径 ../assets/ 会解析到 /api/ppt/decks/assets/）
os.makedirs(PPT_OUTPUT_DIR, exist_ok=True)
os.makedirs(PPT_ASSET_DIR, exist_ok=True)
app.mount("/api/ppt/assets", StaticFiles(directory=str(PPT_ASSET_DIR)), name="ppt_assets")
app.mount("/api/ppt/decks/assets", StaticFiles(directory=str(PPT_ASSET_DIR)), name="ppt_decks_assets")

# favicon 支持：用 logo.png 作为站点图标
from fastapi.responses import FileResponse
@app.get("/favicon.ico")
def favicon():
    return FileResponse(os.path.join(FRONTEND_DIR, "images", "logo.png"))

# 前端静态文件挂载在根路径，API路由优先匹配
app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")

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