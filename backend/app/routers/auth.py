from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole
from app.models.class_ import Class
from app.models.teacher_class import TeacherClass
from app.models.workspace import Workspace
from app.schemas.user import UserLogin, Token, UserResponse, ClassInfo, SelectClassRequest, SelectClassResponse
from app.services.auth import authenticate_user, create_access_token, verify_password, get_password_hash

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", response_model=Token)
async def login(data: UserLogin, db: AsyncSession = Depends(get_db)):
    """用户登录"""
    user = await authenticate_user(db, data.username, data.password)
    if not user:
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    
    available_classes = []
    need_select_class = False
    
    # 判断是否是管理员从评委入口登录
    is_admin_as_judge = (user.role == UserRole.admin and data.login_type == "judge")
    
    # 管理员从管理后台登录
    if user.role == UserRole.admin and data.login_type == "admin":
        result = await db.execute(select(Workspace).where(Workspace.admin_id == user.id))
        workspace = result.scalar_one_or_none()
        if workspace:
            result = await db.execute(select(Class).where(Class.workspace_id == workspace.id))
            classes = result.scalars().all()
            available_classes = [ClassInfo(id=c.id, name=c.name) for c in classes]
        need_select_class = True
        returned_role = UserRole.admin
        
    # 管理员从评委入口登录（作为评委）
    elif is_admin_as_judge:
        result = await db.execute(select(Workspace).where(Workspace.admin_id == user.id))
        workspace = result.scalar_one_or_none()
        if workspace:
            result = await db.execute(select(Class).where(Class.workspace_id == workspace.id))
            classes = result.scalars().all()
            available_classes = [ClassInfo(id=c.id, name=c.name) for c in classes]
        need_select_class = len(available_classes) > 0
        returned_role = UserRole.judge  # 作为评委登录
        
    # 评委角色登录
    elif user.role == UserRole.judge:
        # 评委：获取其所属的所有班级（类似教师）
        result = await db.execute(
            select(Class)
            .join(TeacherClass, TeacherClass.class_id == Class.id)
            .where(TeacherClass.teacher_id == user.id)
        )
        classes = result.scalars().all()
        available_classes = [ClassInfo(id=c.id, name=c.name) for c in classes]
        need_select_class = len(available_classes) > 0
        returned_role = UserRole.judge
        
    # 观众角色登录
    elif user.role == UserRole.audience:
        # 观众：自动进入其所属班级（类似学生）
        if user.class_id:
            result = await db.execute(select(Class).where(Class.id == user.class_id))
            class_ = result.scalar_one_or_none()
            if class_:
                available_classes = [ClassInfo(id=class_.id, name=class_.name)]
        need_select_class = False
        returned_role = UserRole.audience
        
    # 保持向后兼容性：教师角色
    elif user.role == UserRole.teacher:
        # 教师：获取其所属的所有班级
        result = await db.execute(
            select(Class)
            .join(TeacherClass, TeacherClass.class_id == Class.id)
            .where(TeacherClass.teacher_id == user.id)
        )
        classes = result.scalars().all()
        available_classes = [ClassInfo(id=c.id, name=c.name) for c in classes]
        need_select_class = len(available_classes) > 0
        returned_role = UserRole.teacher
        
    # 保持向后兼容性：学生角色
    elif user.role == UserRole.student:
        # 学生：自动进入其所属班级
        if user.class_id:
            result = await db.execute(select(Class).where(Class.id == user.class_id))
            class_ = result.scalar_one_or_none()
            if class_:
                available_classes = [ClassInfo(id=class_.id, name=class_.name)]
        need_select_class = False
        returned_role = UserRole.student
    else:
        returned_role = user.role
    
    access_token = create_access_token(data={"sub": str(user.id), "role": returned_role.value})
    
    # 检查是否使用默认密码
    need_change_password = verify_password("123456", user.password_hash)
    
    # 检查学生或观众是否需要设置主题
    need_set_topic = (returned_role in [UserRole.student, UserRole.audience] and not user.topic)
    
    return Token(
        access_token=access_token,
        user=UserResponse(
            id=user.id,
            username=user.username,
            role=returned_role,
            display_name=user.display_name,
            workspace_id=user.workspace_id,
            class_id=user.class_id,
            topic=user.topic
        ),
        available_classes=available_classes,
        need_select_class=need_select_class,
        need_change_password=need_change_password,
        need_set_topic=need_set_topic
    )


@router.post("/select-class", response_model=SelectClassResponse)
async def select_class(data: SelectClassRequest, user_id: int, db: AsyncSession = Depends(get_db)):
    """选择班级（管理员/教师登录后调用）"""
    # 获取用户
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 验证班级访问权限
    result = await db.execute(select(Class).where(Class.id == data.class_id))
    class_ = result.scalar_one_or_none()
    if not class_:
        raise HTTPException(status_code=404, detail="班级不存在")
    
    if user.role == UserRole.admin:
        # 管理员验证班级属于其工作空间
        result = await db.execute(select(Workspace).where(Workspace.admin_id == user.id))
        workspace = result.scalar_one_or_none()
        if not workspace or class_.workspace_id != workspace.id:
            raise HTTPException(status_code=403, detail="无权访问该班级")
    elif user.role in [UserRole.teacher, UserRole.judge]:
        # 教师和评委验证是否在该班级
        result = await db.execute(
            select(TeacherClass)
            .where(TeacherClass.teacher_id == user.id)
            .where(TeacherClass.class_id == data.class_id)
        )
        if not result.scalar_one_or_none():
            raise HTTPException(status_code=403, detail="无权访问该班级")
    else:
        raise HTTPException(status_code=403, detail="学生和观众不需要选择班级")
    
    # 生成带 class_id 的 token
    access_token = create_access_token(data={
        "sub": str(user.id),
        "role": user.role.value,
        "class_id": data.class_id
    })
    
    return SelectClassResponse(
        access_token=access_token,
        class_id=data.class_id,
        class_name=class_.name
    )


@router.post("/change-password")
async def change_password(
    old_password: str,
    new_password: str,
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """修改密码"""
    # 获取用户
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 验证旧密码
    if not verify_password(old_password, user.password_hash):
        raise HTTPException(status_code=401, detail="原密码错误")
    
    # 不允许设置为默认密码
    if new_password == "123456":
        raise HTTPException(status_code=400, detail="不能使用默认密码")
    
    # 更新密码
    from app.services.auth import get_password_hash
    user.password_hash = get_password_hash(new_password)
    await db.commit()
    
    return {"message": "密码修改成功"}


@router.post("/set-topic")
async def set_topic(
    topic: str,
    user_id: int,
    db: AsyncSession = Depends(get_db)
):
    """设置课题主题"""
    # 获取用户
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 验证是否为学生或观众
    if user.role not in [UserRole.student, UserRole.audience]:
        raise HTTPException(status_code=403, detail="只有学生团队和观众可以设置主题")
    
    # 验证主题不为空
    if not topic or not topic.strip():
        raise HTTPException(status_code=400, detail="主题不能为空")
    
    # 更新主题
    user.topic = topic.strip()
    await db.commit()
    
    return {"message": "主题设置成功", "topic": user.topic}


@router.get("/classes", response_model=list[ClassInfo])
async def get_classes(
    workspace_id: int = Query(1),
    db: AsyncSession = Depends(get_db)
):
    """获取指定工作区的所有班级（无需登录，用于大屏展示）"""
    result = await db.execute(select(Class).where(Class.workspace_id == workspace_id))
    classes = result.scalars().all()
    return [ClassInfo(id=c.id, name=c.name) for c in classes]
