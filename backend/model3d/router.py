# 3D 模型学习记录接口
from fastapi import APIRouter, Header
from model3d.service import mark_model_learned_service, get_learning_stats_service

router = APIRouter()


# 标记模型为已学习
@router.post("/model/{model_id}/learn")
def mark_learned(model_id: str, token: str = Header(...)):
    return mark_model_learned_service(token, model_id)


# 获取当前用户的学习统计
@router.get("/model/learning/stats")
def learning_stats(token: str = Header(...)):
    return get_learning_stats_service(token)
