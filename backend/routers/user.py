#这里是用户接口文件
from fastapi import APIRouter
from service.user import register_user, login_user, delete_user_account, change_user_password
from utils.response import ApiResponse
from model.request import userRegisterRequest, userLoginRequest

router = APIRouter()

#用户注册接口
@router.post("/register")
def register(request: userRegisterRequest):
    result = register_user(request.username, request.password, request.telephone)
    return ApiResponse.success(data=result, msg="注册成功")

#用户登录接口
@router.post("/login")
def login(request: userLoginRequest):
    result = login_user(request.username, request.password)
    return ApiResponse.success(data=result, msg="登录成功")
