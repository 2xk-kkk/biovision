#这里是用户接口文件
from fastapi import APIRouter, Header
from service.user import register_user, login_user, delete_user_account, change_user_password, get_user_profile, update_user_username, update_user_avatar, update_user_introduction, get_user_statistics, follow_user_service, unfollow_user_service, check_follow_status, increment_profile_view, get_user_followers, get_user_following
from utils.response import ApiResponse
from model.request import userRegisterRequest, userLoginRequest, changeUsernameRequest, changeAvatarRequest, changeIntroductionRequest
from utils.jwt_utils import verify_jwt

router = APIRouter()

#用户注册接口
@router.post("/register")
def register(request: userRegisterRequest):
    return register_user(request.username, request.password, request.telephone)

#用户登录接口
@router.post("/login")
def login(request: userLoginRequest):
    return login_user(request.username, request.password)

#获取用户信息接口
@router.get("/user/{user_id}/info")
def get_user_info(user_id: int):
    return get_user_profile(user_id)

#修改用户名接口
@router.put("/user/{user_id}/username")
def update_username(user_id: int, request: changeUsernameRequest, token: str = Header(...)):
    payload = verify_jwt(token)
    if not payload["success"]:
        return ApiResponse.error(msg="请先登录")
    
    if int(payload["msg"]["user_id"]) != user_id:
        return ApiResponse.error(msg="无权限")
    
    return update_user_username(user_id, request.new_username)

#更新头像接口
@router.put("/user/{user_id}/avatar")
def update_avatar(user_id: int, request: changeAvatarRequest, token: str = Header(...)):
    payload = verify_jwt(token)
    if not payload["success"]:
        return ApiResponse.error(msg="请先登录")
    
    if int(payload["msg"]["user_id"]) != user_id:
        return ApiResponse.error(msg="无权限")
    
    return update_user_avatar(user_id, request.avatar_data)

#更新个人简介接口
@router.put("/user/{user_id}/introduction")
def update_introduction(user_id: int, request: changeIntroductionRequest, token: str = Header(...)):
    payload = verify_jwt(token)
    if not payload["success"]:
        return ApiResponse.error(msg="请先登录")
    
    if int(payload["msg"]["user_id"]) != user_id:
        return ApiResponse.error(msg="无权限")
    
    return update_user_introduction(user_id, request.introduction)

#获取用户统计数据接口
@router.get("/user/{user_id}/stats")
def get_stats(user_id: int):
    return get_user_statistics(user_id)

#关注用户接口
@router.post("/user/{user_id}/follow")
def follow(user_id: int, token: str = Header(...)):
    payload = verify_jwt(token)
    if not payload["success"]:
        return ApiResponse.error(msg="请先登录")
    
    follower_id = int(payload["msg"]["user_id"])
    return follow_user_service(follower_id, user_id)

#取消关注接口
@router.post("/user/{user_id}/unfollow")
def unfollow(user_id: int, token: str = Header(...)):
    payload = verify_jwt(token)
    if not payload["success"]:
        return ApiResponse.error(msg="请先登录")
    
    follower_id = int(payload["msg"]["user_id"])
    return unfollow_user_service(follower_id, user_id)

#检查关注状态接口
@router.get("/user/{user_id}/follow/status")
def check_follow(user_id: int, token: str = Header(...)):
    payload = verify_jwt(token)
    if not payload["success"]:
        return ApiResponse.error(msg="请先登录")
    
    follower_id = int(payload["msg"]["user_id"])
    return check_follow_status(follower_id, user_id)

#增加主页浏览量接口
@router.post("/user/{user_id}/view")
def add_view(user_id: int, token: str = Header(None)):
    return increment_profile_view(user_id)

#获取粉丝列表接口
@router.get("/user/{user_id}/followers")
def get_followers(user_id: int):
    return get_user_followers(user_id)

#获取关注列表接口
@router.get("/user/{user_id}/following")
def get_following(user_id: int):
    return get_user_following(user_id)
