# 3D 模型收藏接口
from fastapi import APIRouter, Header
from service.model import (
    toggle_model_favorite_service,
    get_favorited_model_ids_service,
    get_user_model_favorites_service,
)

router = APIRouter()


# 切换收藏（收藏 / 取消收藏）
@router.post("/model/{model_id}/favorite")
def toggle_favorite(model_id: str, token: str = Header(...)):
    return toggle_model_favorite_service(token, model_id)


# 获取当前用户已收藏的模型 id 列表
@router.get("/model/favorites/ids")
def favorited_ids(token: str = Header(...)):
    return get_favorited_model_ids_service(token)


# 获取用户收藏的模型详情列表
@router.get("/user/{user_id}/model-favorites")
def user_model_favorites(user_id: int):
    return get_user_model_favorites_service(user_id)
