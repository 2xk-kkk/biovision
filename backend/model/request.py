from pydantic import BaseModel, Field
from typing import List

class userLoginRequest(BaseModel):
    username: str=Field(min_length=1, max_length=20, example="张三", description="用户名,长度为1-20个字符")
    password: str=Field(min_length=6, max_length=20, example="a123456", description="密码,长度为6-20个字符,必须包含字母和数字")
    
class userRegisterRequest(userLoginRequest):
    telephone: str=Field(min_length=1, max_length=20, example="13800138000", description="电话号码")

class changePasswordRequest(BaseModel):
    new_password: str=Field(min_length=6, max_length=20, example="a123456", description="新密码,长度为6-20个字符,必须包含字母和数字")

class changeUsernameRequest(BaseModel):
    new_username: str=Field(min_length=2, max_length=20, example="新用户名", description="新用户名,长度为2-20个字符")

class changeAvatarRequest(BaseModel):
    avatar_data: str=Field(example="data:image/png;base64,iVBORw0KGgo...", description="头像数据(Base64编码)")

class changeIntroductionRequest(BaseModel):
    introduction: str=Field(example="这是我的个人简介...", description="个人简介")

class changeIpAddressRequest(BaseModel):
    ip_address: str=Field(example="北京", description="IP地址（城市名称）")

class updateUserInfoRequest(BaseModel):
    school: str = Field(None, example="成都东软学院", description="学校")
    grade: str = Field(None, example="高一", description="年级")
    role: str = Field(None, example="学生", description="身份")
    introduction: str = Field(None, example="这是我的个人简介", description="个人简介")
    ip_address: str = Field(None, example="北京", description="IP地址（城市名称）")

from pydantic import BaseModel
class CreatePostRequest(BaseModel):
    content: str
    tag: str = "Question_discussion"
    image_urls: List[str] = []
    tags: List[str] = []
    file_urls: List[str] = []

class CreateCommentRequest(BaseModel):
    content: str
    parent_id: int = None