import time
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole
from app.models.system_settings import SystemSettings, SystemStage
from app.models.class_ import Class
from app.models.teacher_class import TeacherClass
from app.models.contest import Contest
from app.models.vote_record import VoteRecord
from app.models.judge_score import JudgeScore
from app.schemas.user import UserResponse, UserCreate, UserImport
from app.schemas.system import StageSetRequest, SystemStateResponse, ScoreProgressResponse
from app.services.auth import get_password_hash
from app.websocket import manager

router = APIRouter(prefix="/admin", tags=["管理员"])


@router.get("/students", response_model=list[UserResponse])
async def get_students(class_id: int = Query(...), db: AsyncSession = Depends(get_db)):
    """获取赛场内的所有观众"""
    result = await db.execute(
        select(User)
        .where(User.class_id == class_id)
        .where(User.role == UserRole.audience)
    )
    return result.scalars().all()





@router.post("/students", response_model=UserResponse)
async def create_student(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """手动创建单个观众账号"""
    # 检查用户名是否存在
    result = await db.execute(select(User).where(User.username == data.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")
        
    user = User(
        username=data.username,
        password_hash=get_password_hash(data.password),
        role=UserRole.audience,
        display_name=data.display_name or data.username,
        class_id=data.class_id,
        workspace_id=1
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/students/import", status_code=201)
async def import_students(data: UserImport, db: AsyncSession = Depends(get_db)):
    """批量导入观众账号"""
    success_count = 0
    errors = []
    
    for item in data.users:
        # 检查用户名是否存在
        result = await db.execute(select(User).where(User.username == item.username))
        if result.scalar_one_or_none():
            errors.append(f"用户 {item.username} 已存在")
            continue
            
        user = User(
            username=item.username,
            password_hash=get_password_hash(item.password),
            role=UserRole.audience,
            display_name=item.display_name or item.username,
            class_id=data.class_id,
            workspace_id=1
        )
        db.add(user)
        success_count += 1
        
    await db.commit()
    
    return {
        "message": f"成功导入 {success_count} 个账号",
        "errors": errors
    }


@router.get("/teachers", response_model=list[UserResponse])
async def get_teachers(class_id: int = Query(...), db: AsyncSession = Depends(get_db)):
    """获取赛场内的所有评委"""
    # 通过 TeacherClass 关联表查询
    result = await db.execute(
        select(User)
        .join(TeacherClass, TeacherClass.teacher_id == User.id)
        .where(TeacherClass.class_id == class_id)
    )
    return result.scalars().all()


@router.post("/teachers", response_model=UserResponse)
async def create_teacher(data: UserCreate, db: AsyncSession = Depends(get_db)):
    """创建评委并添加到赛场"""
    # 检查用户名是否存在
    result = await db.execute(select(User).where(User.username == data.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")
        
    user = User(
        username=data.username,
        password_hash=get_password_hash(data.password),
        role=UserRole.judge, # 使用 judge 角色
        display_name=data.display_name,
        workspace_id=1
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    # 如果指定了 class_id，关联到赛场
    if data.class_id:
        tc = TeacherClass(teacher_id=user.id, class_id=data.class_id)
        db.add(tc)
        await db.commit()
        
    return user


@router.post("/teachers/add")
async def add_teacher_to_class(class_id: int = Query(...), teacher_id: int = Query(...), db: AsyncSession = Depends(get_db)):
    """将现有评委添加到赛场"""
    # 检查是否已存在
    result = await db.execute(
        select(TeacherClass)
        .where(TeacherClass.class_id == class_id)
        .where(TeacherClass.teacher_id == teacher_id)
    )
    if result.scalar_one_or_none():
        return {"message": "评委已在赛场中"}
        
    tc = TeacherClass(teacher_id=teacher_id, class_id=class_id)
    db.add(tc)
    await db.commit()
    return {"message": "添加成功"}


@router.delete("/teachers/{teacher_id}")
async def remove_teacher_from_class(teacher_id: int, class_id: int = Query(...), db: AsyncSession = Depends(get_db)):
    """从赛场移除评委"""
    await db.execute(
        delete(TeacherClass)
        .where(TeacherClass.class_id == class_id)
        .where(TeacherClass.teacher_id == teacher_id)
    )
    await db.commit()
    return {"message": "移除成功"}


@router.delete("/users/{user_id}")
async def delete_user(user_id: int, db: AsyncSession = Depends(get_db)):
    """删除用户"""
    # 获取用户以检查角色（可选）
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
        
    # 如果是评委，还要删除关联
    if user.role == UserRole.judge:
        await db.execute(delete(TeacherClass).where(TeacherClass.teacher_id == user_id))
        
    await db.delete(user)
    await db.commit()
    return {"message": "删除成功"}


@router.get("/teams", response_model=list[UserResponse])
async def get_teams(class_id: int = Query(...), db: AsyncSession = Depends(get_db)):
    """获取可用的辩手/队伍"""
    # 实际上就是获取所有用户，这里可以用来做辞手列表
    # 辩论赛系统中，辩手也是一种User，或者我们可以通过 get_users 获取所有
    # 为了兼容前端，返回所有该班级的用户（除了admin）
    result = await db.execute(
        select(User)
        .where(User.class_id == class_id)
        .where(User.role.in_([UserRole.student, UserRole.judge, UserRole.audience])) 
    )
    return result.scalars().all()


@router.get("/state", response_model=SystemStateResponse)
async def get_system_state(class_id: int = Query(...), db: AsyncSession = Depends(get_db)):
    """获取当前班级的系统状态"""
    result = await db.execute(select(SystemSettings).where(SystemSettings.class_id == class_id))
    settings = result.scalar_one_or_none()
    
    if not settings:
        # 创建该班级的默认状态
        settings = SystemSettings(class_id=class_id)
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    
    # 获取当前团队名称和主题
    team_name = None
    team_topic = None
    if settings.current_team_id:
        team_result = await db.execute(select(User).where(User.id == settings.current_team_id))
        team = team_result.scalar_one_or_none()
        if team:
            team_name = team.display_name
            team_topic = team.topic
    
    # 获取当前倒计时
    current_countdown = manager.get_countdown(class_id)
    
    # 辩论赛系统不需要教师评分平均分和完成状态，这里返回默认值
    teacher_avg_score = None
    student_avg_score = None
    teacher_scoring_completed = False
    student_scoring_completed = False
    
    return SystemStateResponse(
        class_id=settings.class_id,
        current_stage=settings.current_stage,
        current_team_id=settings.current_team_id,
        current_team_name=team_name,
        current_team_topic=team_topic,
        snatch_slots_remaining=settings.snatch_slots_remaining,
        snatch_start_time=settings.snatch_start_time,
        countdown=manager.get_countdown(class_id),
        teacher_avg_score=teacher_avg_score,
        student_avg_score=student_avg_score,
        teacher_scoring_completed=teacher_scoring_completed,
        student_scoring_completed=student_scoring_completed,
        update_time=settings.update_time
    )


@router.post("/stage/set", response_model=SystemStateResponse)
async def set_stage(data: StageSetRequest, class_id: int = Query(...), db: AsyncSession = Depends(get_db)):
    """设置系统阶段"""
    result = await db.execute(select(SystemSettings).where(SystemSettings.class_id == class_id))
    settings = result.scalar_one_or_none()
    
    if not settings:
        settings = SystemSettings(class_id=class_id)
        db.add(settings)
    
    settings.current_stage = data.stage
    settings.update_time = int(time.time() * 1000)
    
    if data.target_team_id is not None:
        settings.current_team_id = data.target_team_id
    
    await db.commit()
    await db.refresh(settings)
    
    # 获取当前团队信息
    team_name = None
    team_topic = None
    if settings.current_team_id:
        team_result = await db.execute(select(User).where(User.id == settings.current_team_id))
        team = team_result.scalar_one_or_none()
        if team:
            team_name = team.display_name
            team_topic = team.topic
            
    # 构造 WebSocket 消息数据
    state_data = {
        "class_id": settings.class_id,
        "current_stage": settings.current_stage,
        "current_team_id": settings.current_team_id,
        "current_team_name": team_name,
        "current_team_topic": team_topic,
        "snatch_slots_remaining": settings.snatch_slots_remaining,
        "countdown": manager.get_countdown(class_id),
        "teacher_avg_score": None,
        "student_avg_score": None,
        "update_time": settings.update_time
    }
    
    # 广播状态更新
    await manager.broadcast_to_class(class_id, {
        "type": "STATE_UPDATE",
        "data": state_data
    })
    
    return SystemStateResponse(
        class_id=settings.class_id,
        current_stage=settings.current_stage,
        current_team_id=settings.current_team_id,
        current_team_name=team_name,
        current_team_topic=team_topic,
        snatch_slots_remaining=settings.snatch_slots_remaining,
        snatch_start_time=settings.snatch_start_time,
        countdown=manager.get_countdown(class_id),
        teacher_avg_score=None,
        student_avg_score=None,
        teacher_scoring_completed=False,
        student_scoring_completed=False,
        update_time=settings.update_time
    )


@router.get("/progress", response_model=ScoreProgressResponse)
async def get_progress(class_id: int = Query(...), db: AsyncSession = Depends(get_db)):
    """获取评分进度 - 辩论赛版本返回空数据"""
    return ScoreProgressResponse(
        submitted_count=0,
        total_count=0,
        not_submitted=[]
    )


# ===== 辩论赛专用接口 =====

@router.post("/debate/contest")
async def create_contest(
    topic: str = Query(...),
    pro_team_name: str = Query(...),
    con_team_name: str = Query(...),
    class_id: int = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """创建新的辩论比赛"""
    contest = Contest(
        class_id=class_id,
        topic=topic,
        pro_team_name=pro_team_name,
        con_team_name=con_team_name
    )
    db.add(contest)
    await db.commit()
    await db.refresh(contest)
    return contest


@router.get("/debate/contest")
async def get_current_contest(
    class_id: int = Query(...), 
    db: AsyncSession = Depends(get_db)
):
    """获取班级当前的最新比赛"""
    result = await db.execute(
        select(Contest)
        .where(Contest.class_id == class_id)
        .order_by(Contest.created_at.desc())
        .limit(1)
    )
    contest = result.scalar_one_or_none()
    if not contest:
        raise HTTPException(status_code=404, detail="未找到比赛配置")
    return {"contest": contest}


@router.post("/debate/stage")
async def set_debate_stage(
    stage: str = Query(...),
    class_id: int = Query(...),
    contest_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """设置辩论赛阶段"""
    result = await db.execute(select(SystemSettings).where(SystemSettings.class_id == class_id))
    settings = result.scalar_one_or_none()
    
    if not settings:
        settings = SystemSettings(class_id=class_id)
        db.add(settings)
    
    settings.current_stage = stage
    settings.update_time = int(time.time() * 1000)
    
    await db.commit()
    
    await manager.broadcast_to_class(class_id, {
        "type": "STATE_UPDATE",
        "data": {
            "current_stage": stage,
            "update_time": settings.update_time
        }
    })
    
    return {"message": "Stage updated"}


@router.get("/debate/progress")
async def get_debate_progress(
    class_id: int = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """获取投票和评分进度"""
    result = await db.execute(
        select(Contest)
        .where(Contest.class_id == class_id)
        .order_by(Contest.created_at.desc())
        .limit(1)
    )
    contest = result.scalar_one_or_none()
    
    if not contest:
        return {}
        
    contest_id = contest.id
    
    audience_count_res = await db.execute(
        select(func.count(User.id))
        .where(User.class_id == class_id)
        .where(User.role == UserRole.audience)
    )
    total_audience = audience_count_res.scalar() or 0
    
    pre_votes_res = await db.execute(
        select(func.count(VoteRecord.id))
        .where(VoteRecord.contest_id == contest_id)
        .where(VoteRecord.vote_type == "pre_contest")
    )
    pre_submitted = pre_votes_res.scalar() or 0
    
    post_votes_res = await db.execute(
        select(func.count(VoteRecord.id))
        .where(VoteRecord.contest_id == contest_id)
        .where(VoteRecord.vote_type == "post_contest")
    )
    post_submitted = post_votes_res.scalar() or 0
    
    judge_count_res = await db.execute(
        select(func.count(TeacherClass.teacher_id))
        .where(TeacherClass.class_id == class_id)
    )
    total_judges = judge_count_res.scalar() or 0
    
    judges_submitted_res = await db.execute(
        select(func.count(func.distinct(JudgeScore.judge_id)))
        .where(JudgeScore.contest_id == contest_id)
    )
    items_submitted = judges_submitted_res.scalar() or 0
    
    return {
        "voting_enabled": {
            "pre_voting": True,
            "post_voting": True,
            "judge_scoring": True
        },
        "pre_voting_progress": {
            "total": total_audience,
            "submitted": pre_submitted,
            "percentage": int(pre_submitted / total_audience * 100) if total_audience > 0 else 0
        },
        "post_voting_progress": {
            "total": total_audience,
            "submitted": post_submitted,
            "percentage": int(post_submitted / total_audience * 100) if total_audience > 0 else 0
        },
        "judge_scoring_progress": {
            "total": total_judges,
            "submitted": items_submitted,
            "percentage": int(items_submitted / total_judges * 100) if total_judges > 0 else 0
        }
    }


@router.post("/debate/reveal-results")
async def reveal_debate_results(
    class_id: int = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """揭晓比赛结果"""
    result = await db.execute(select(SystemSettings).where(SystemSettings.class_id == class_id))
    settings = result.scalar_one_or_none()
    
    if settings:
        settings.current_stage = "RESULTS_REVEALED"
        settings.update_time = int(time.time() * 1000)
        await db.commit()
        
        await manager.broadcast_to_class(class_id, {
            "type": "STATE_UPDATE",
            "data": {
                "current_stage": "RESULTS_REVEALED"
            }
        })
    return {"message": "Results revealed"}


@router.put("/users/{user_id}/debate-role")
async def update_user_debate_role(
    user_id: int,
    team_side: str | None = Query(None),
    debater_position: str | None = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """更新用户的辩论角色（分配辩手）"""
    user = await db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if team_side:
        user.team_side = team_side
        
    if debater_position:
        user.debater_position = debater_position
        
    await db.commit()
    return {"message": "Role updated"}