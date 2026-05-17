# routers/chart.py
from fastapi import APIRouter
from service.chart import get_forum_stats  # 调用统计逻辑

# 创建路由
router = APIRouter()

# 论坛统计接口 → 前端访问：/api/stats
@router.get("/stats")
def get_stats():
    return get_forum_stats()