# 3D 模型学习记录：业务逻辑
from database.db import get_db_connection
from utils.jwt_utils import verify_jwt
from utils.response import ApiResponse
from model.model_favorite import get_model_info
from model3d.models import mark_model_learned, get_user_learning_stats


# 标记模型为已学习
def mark_model_learned_service(token, model_id):
    if not get_model_info(model_id):
        return ApiResponse.error(msg="模型不存在")
    payload = verify_jwt(token)
    if not payload["success"]:
        return ApiResponse.error(msg="请先登录")
    user_id = int(payload["msg"]["user_id"])

    db = get_db_connection()
    try:
        mark_model_learned(db, user_id, model_id)
        return ApiResponse.success(
            data={"model_id": model_id, "learned": True},
            msg="已记录学习",
        )
    finally:
        db.close()


# 获取当前用户的学习统计（已学习数量 + 完成率）
def get_learning_stats_service(token):
    payload = verify_jwt(token)
    if not payload["success"]:
        return ApiResponse.error(msg="请先登录")
    user_id = int(payload["msg"]["user_id"])

    db = get_db_connection()
    try:
        stats = get_user_learning_stats(db, user_id)
        return ApiResponse.success(data=stats)
    finally:
        db.close()
