"""
初始化数据库脚本
创建默认管理员账号和工作空间
使用 --data 参数可创建测试班级和用户
"""
import argparse
import asyncio
import subprocess
import sys
from sqlalchemy import select

from app.database import async_session, init_db
from app.models.user import User, UserRole
from app.models.workspace import Workspace
from app.models.teacher_class import TeacherClass
from app.models.class_ import Class
from app.models.system_settings import SystemSettings, SystemStage
from app.services.auth import get_password_hash


async def create_default_admin():
    """创建默认管理员账号和工作空间，返回工作空间ID"""
    async with async_session() as db:
        # 检查是否已存在管理员
        result = await db.execute(select(User).where(User.role == UserRole.admin))
        existing_admin = result.scalar_one_or_none()
        
        if existing_admin:
            print("管理员账号已存在，跳过创建")
            # 获取工作空间ID
            result = await db.execute(select(Workspace).where(Workspace.admin_id == existing_admin.id))
            workspace = result.scalar_one_or_none()
            return workspace.id if workspace else None
        
        # 创建管理员账号
        admin = User(
            username="admin",
            password_hash=get_password_hash("admin"),
            role=UserRole.admin,
            display_name="管理员"
        )
        db.add(admin)
        await db.commit()
        await db.refresh(admin)
        
        # 创建默认工作空间
        workspace = Workspace(
            name="秦振凯的工作空间",
            admin_id=admin.id
        )
        db.add(workspace)
        await db.commit()
        await db.refresh(workspace)
        
        # 更新管理员的工作空间关联
        admin.workspace_id = workspace.id
        await db.commit()
        
        print(f"创建管理员账号成功: qzk / 123456")
        print(f"创建工作空间成功: {workspace.name} (ID: {workspace.id})")
        return workspace.id


async def create_test_data(workspace_id: int):
    """创建测试班级、教师和学生团队"""
    async with async_session() as db:
        # 检查是否已有测试数据
        result = await db.execute(select(Class).where(Class.workspace_id == workspace_id))
        existing_classes = result.scalars().all()
        if existing_classes:
            print("测试班级已存在，跳过创建")
            return
        
        # 创建比赛场次
        class_names = ["初赛", "决赛"]
        classes = []
        for name in class_names:
            class_ = Class(
                name=name,
                workspace_id=workspace_id
            )
            db.add(class_)
            classes.append(class_)
        await db.commit()
        
        for class_ in classes:
            await db.refresh(class_)
            # 创建班级的系统设置
            settings = SystemSettings(class_id=class_.id, current_stage=SystemStage.IDLE)
            db.add(settings)
        await db.commit()
        
        print(f"创建班级成功: {', '.join(class_names)}")
        
        # 将空间管理员添加进入评委列表
        result = await db.execute(select(Workspace).where(Workspace.id == workspace_id))
        workspace = result.scalar_one_or_none()
        if not workspace:
            raise HTTPException(status_code=404, detail="工作空间不存在")
        
        # 将工作空间管理员添加到班级评委列表
        if workspace.admin_id:
            tc = TeacherClass(teacher_id=workspace.admin_id, class_id=class_.id)
            db.add(tc)
        await db.commit()


        # 为每个班级创建学生团队
        for class_ in classes:
            for i in range(1, 5):
                team = User(
                    username=f"team{i:02d}_{class_.id}",
                    password_hash=get_password_hash("123456"),
                    role=UserRole.student,
                    display_name=f"团队{i}",
                    workspace_id=workspace_id,
                    class_id=class_.id
                )
                db.add(team)
            await db.commit()
            print(f"创建 {class_.name} 学生团队成功: team01-04 / 123456")


async def main(create_data: bool = False):
    # 初始化数据库表
    await init_db()
    print("数据库表创建成功")

    # 标记 alembic 版本为最新，防止后续 migration 冲突
    try:
        print("正在同步 Alembic 版本...")
        subprocess.run([sys.executable, "-m", "alembic", "stamp", "head"], check=True)
        print("Alembic 版本已同步到 head")
    except subprocess.CalledProcessError as e:
        print(f"同步 Alembic 版本失败: {e}")
    except Exception as e:
        print(f"发生意外错误: {e}")
    
    # 创建默认管理员
    workspace_id = await create_default_admin()
    
    # 如果指定了 --data 参数，创建测试数据
    if create_data and workspace_id:
        await create_test_data(workspace_id)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="初始化数据库")
    parser.add_argument("--data", action="store_true", help="创建测试班级和用户数据")
    args = parser.parse_args()
    
    asyncio.run(main(create_data=args.data))
