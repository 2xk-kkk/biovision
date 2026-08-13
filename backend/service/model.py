# 3D 模型收藏业务逻辑
from database.db import get_db_connection
from utils.jwt_utils import verify_jwt
from utils.response import ApiResponse
from model.model_favorite import (
    get_model_info,
    toggle_model_favorite,
    get_user_favorited_model_ids,
    get_user_model_favorites,
)


# 切换收藏（收藏 / 取消收藏）
def toggle_model_favorite_service(token, model_id):
    if not get_model_info(model_id):
        return ApiResponse.error(msg="模型不存在")
    payload = verify_jwt(token)
    if not payload["success"]:
        return ApiResponse.error(msg="请先登录")
    user_id = int(payload["msg"]["user_id"])

    db = get_db_connection()
    try:
        status = toggle_model_favorite(db, user_id, model_id)
        return ApiResponse.success(
            data={"model_id": model_id, "is_favorited": status},
            msg="收藏成功" if status else "已取消收藏",
        )
    finally:
        db.close()


# 获取当前用户已收藏的模型 id 列表
def get_favorited_model_ids_service(token):
    payload = verify_jwt(token)
    if not payload["success"]:
        return ApiResponse.error(msg="请先登录")
    user_id = int(payload["msg"]["user_id"])

    db = get_db_connection()
    try:
        ids = get_user_favorited_model_ids(db, user_id)
        return ApiResponse.success(data={"model_ids": ids})
    finally:
        db.close()


# 获取用户收藏的模型详情列表
def get_user_model_favorites_service(user_id):
    db = get_db_connection()
    try:
        favorites = get_user_model_favorites(db, user_id)
        return ApiResponse.success(data=favorites)
    finally:
        db.close()
