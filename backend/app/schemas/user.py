from pydantic import BaseModel
from app.models.user import UserRole


class UserCreate(BaseModel):
    username: str
    password: str
    role: UserRole
    display_name: str | None = None
    class_id: int | None = None  # 学生团队需要指定班级


class StudentCreate(BaseModel):
    """创建学生团队的请求体"""
    username: str
    password: str
    display_name: str
    class_id: int | None = None
    topic: str | None = None


class UserImport(BaseModel):
    """批量导入用户请求"""
    class_id: int
    users: list[UserCreate]


class UserResponse(BaseModel):
    id: int
    username: str
    role: UserRole
    display_name: str
    workspace_id: int | None = None
    class_id: int | None = None
    has_presented: bool = False
    topic: str | None = None
    
    class Config:
        from_attributes = True


class UserLogin(BaseModel):
    username: str
    password: str
    login_type: str = "teacher"  # "admin" 或 "teacher"，默认为评委入口


class ClassInfo(BaseModel):
    """班级简要信息"""
    id: int
    name: str
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
    # 登录时返回可选的班级列表（教师/管理员用）
    available_classes: list[ClassInfo] = []
    # 是否需要选择班级
    need_select_class: bool = False
    # 是否需要修改密码（默认密码登录时）
    need_change_password: bool = False
    # 是否需要设置课题主题（学生）
    need_set_topic: bool = False


class SelectClassRequest(BaseModel):
    class_id: int


class SelectClassResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    class_id: int
    class_name: str
