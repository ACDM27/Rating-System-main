from pydantic import BaseModel


class WorkspaceCreate(BaseModel):
    name: str


class WorkspaceResponse(BaseModel):
    id: int
    name: str
    admin_id: int
    
    class Config:
        from_attributes = True


class ClassCreate(BaseModel):
    name: str


class ClassResponse(BaseModel):
    id: int
    name: str
    workspace_id: int
    
    class Config:
        from_attributes = True


class TeacherClassCreate(BaseModel):
    """添加教师到班级"""
    teacher_id: int | None = None  # 如果提供，从其他班级选择已有教师
    # 如果 teacher_id 为空，则创建新教师
    username: str | None = None
    password: str | None = None
    display_name: str | None = None


class TeacherClassResponse(BaseModel):
    id: int
    teacher_id: int
    class_id: int
    teacher_display_name: str
    teacher_username: str
    is_admin: bool = False
    
    class Config:
        from_attributes = True
