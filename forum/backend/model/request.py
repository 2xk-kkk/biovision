from pydantic import BaseModel, Field

class userLoginRequest(BaseModel):
    username: str=Field(min_length=1, max_length=20, example="张三", description="用户名,长度为1-20个字符")
    password: str=Field(min_length=6, max_length=20, example="a123456", description="密码,长度为6-20个字符,必须包含字母和数字")
    
class userRegisterRequest(userLoginRequest):
    telephone: str=Field(min_length=1, max_length=20, example="13800138000", description="电话号码")

class changePasswordRequest(BaseModel):
    new_password: str=Field(min_length=6, max_length=20, example="a123456", description="新密码,长度为6-20个字符,必须包含字母和数字")

from pydantic import BaseModel
class CreatePostRequest(BaseModel):
    content: str
    image_urls: list[str] = []