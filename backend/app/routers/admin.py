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
from app.services.system_state import update_debate_stage
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
        "success_count": success_count,
        "created_count": success_count,  # 保持与评委导入一致
        "errors": errors,
        "message": f"成功导入 {success_count} 个账号" + (f"，{len(errors)} 个失败" if errors else "")
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


@router.post("/teachers/import")
async def import_teachers(data: UserImport, db: AsyncSession = Depends(get_db)):
    """批量导入评委"""
    created_count = 0
    errors = []
    
    for teacher_data in data.users:
        try:
            # 检查用户名是否存在
            result = await db.execute(select(User).where(User.username == teacher_data.username))
            if result.scalar_one_or_none():
                errors.append(f"用户名 {teacher_data.username} 已存在")
                continue
            
            user = User(
                username=teacher_data.username,
                password_hash=get_password_hash(teacher_data.password or '123456'),
                role=UserRole.judge,
                display_name=teacher_data.display_name,
                workspace_id=1
            )
            db.add(user)
            await db.flush()  # 获取user.id
            
            # 关联到赛场
            if teacher_data.class_id:
                tc = TeacherClass(teacher_id=user.id, class_id=teacher_data.class_id)
                db.add(tc)
            
            created_count += 1
        except Exception as e:
            errors.append(f"创建 {teacher_data.username} 失败: {str(e)}")
    
    await db.commit()
    
    return {
        "created_count": created_count,
        "errors": errors,
        "message": f"成功导入 {created_count} 个评委" + (f"，{len(errors)} 个失败" if errors else "")
    }


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


# ===== 场次管理接口 =====

@router.post("/classes")
async def create_class(
    name: str = Query(...),
    workspace_id: int = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """创建新的比赛场次"""
    # 检查场次名称是否已存在
    result = await db.execute(
        select(Class)
        .where(Class.workspace_id == workspace_id)
        .where(Class.name == name)
    )
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="场次名称已存在")
    
    # 创建场次
    class_ = Class(
        name=name,
        workspace_id=workspace_id
    )
    db.add(class_)
    await db.commit()
    await db.refresh(class_)
    
    # 为新场次创建系统设置
    settings = SystemSettings(
        class_id=class_.id,
        current_stage=SystemStage.IDLE
    )
    db.add(settings)
    await db.commit()
    
    return {
        "id": class_.id,
        "name": class_.name,
        "workspace_id": class_.workspace_id,
        "message": "场次创建成功"
    }


@router.get("/classes")
async def get_classes(
    workspace_id: int = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """获取工作空间的所有场次"""
    result = await db.execute(
        select(Class).where(Class.workspace_id == workspace_id)
    )
    classes = result.scalars().all()
    return [
        {
            "id": c.id,
            "name": c.name,
            "workspace_id": c.workspace_id
        }
        for c in classes
    ]


@router.delete("/classes/{class_id}")
async def delete_class(
    class_id: int,
    db: AsyncSession = Depends(get_db)
):
    """删除场次（会级联删除相关数据）"""
    class_ = await db.get(Class, class_id)
    if not class_:
        raise HTTPException(status_code=404, detail="场次不存在")
    
    await db.delete(class_)
    await db.commit()
    return {"message": "场次删除成功"}


# ===== 辩论赛专用接口 =====

@router.post("/debate/contest")
async def create_contest(
    topic: str = Query(...),
    pro_team_name: str = Query(...),
    con_team_name: str = Query(...),
    class_id: int = Query(...),
    pro_topic: str | None = Query(None),
    con_topic: str | None = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """创建新的辩论比赛"""
    contest = Contest(
        class_id=class_id,
        topic=topic,
        pro_team_name=pro_team_name,
        con_team_name=con_team_name,
        pro_topic=pro_topic,
        con_topic=con_topic
    )
    db.add(contest)
    await db.flush()  # 获取 contest.id
    
    # 更新系统设置中的当前比赛ID
    result = await db.execute(select(SystemSettings).where(SystemSettings.class_id == class_id))
    settings = result.scalar_one_or_none()
    
    if not settings:
        settings = SystemSettings(class_id=class_id)
        db.add(settings)
    
    settings.contest_id = contest.id
    settings.update_time = int(time.time() * 1000)
    
    await db.commit()
    await db.refresh(contest)
    
    # 获取更新后的设置以确保数据完整
    await db.refresh(settings)

    # 广播状态更新，通知所有端有了新的比赛
    await manager.broadcast_debate_update(
        stage=settings.current_stage.value if settings.current_stage else "IDLE",
        contest={
            "id": contest.id,
            "topic": contest.topic,
            "pro_team_name": contest.pro_team_name,
            "con_team_name": contest.con_team_name,
            "pro_topic": contest.pro_topic,
            "con_topic": contest.con_topic
        },
        class_id=class_id,
        voting_enabled={
            "pre_voting": settings.pre_voting_enabled,
            "post_voting": settings.post_voting_enabled,
            "judge_scoring": settings.judge_scoring_enabled
        },
        results_revealed=settings.results_revealed,
        progress={}, # 新比赛无进度
        update_time=settings.update_time
    )

    return contest


@router.get("/debate/contest")
async def get_current_contest(
    class_id: int = Query(...), 
    db: AsyncSession = Depends(get_db)
):
    """获取班级当前的最新比赛"""
    # 优先从系统设置中获取当前激活的比赛ID
    settings_result = await db.execute(
        select(SystemSettings).where(SystemSettings.class_id == class_id)
    )
    settings = settings_result.scalar_one_or_none()
    
    contest = None
    if settings and settings.contest_id:
        # 如果系统设置指明了当前比赛，直接获取该比赛
        contest_result = await db.execute(
            select(Contest).where(Contest.id == settings.contest_id)
        )
        contest = contest_result.scalar_one_or_none()
        
    if not contest:
        # 如果没有指定或指定的比赛不存在，降级为获取最新创建的比赛
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


@router.get("/debate/contest/{contest_id}")
async def get_contest_by_id(
    contest_id: int,
    db: AsyncSession = Depends(get_db)
):
    """根据比赛ID获取比赛信息"""
    result = await db.execute(
        select(Contest).where(Contest.id == contest_id)
    )
    contest = result.scalar_one_or_none()
    if not contest:
        raise HTTPException(status_code=404, detail="比赛不存在")
    return contest


@router.post("/debate/stage")
async def set_debate_stage(
    stage: str = Query(...),
    class_id: int = Query(...),
    contest_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """设置辩论赛阶段"""
    try:
        # 尝试将字符串转换为枚举，确保有效性
        stage_enum = SystemStage(stage)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"无效的阶段: {stage}")

    # 使用服务层函数统一处理状态更新
    success = await update_debate_stage(db, class_id, stage_enum, contest_id)
    
    if not success:
        raise HTTPException(status_code=500, detail="更新状态失败")
    
    return {"message": "Stage updated"}


@router.get("/debate/progress")
async def get_debate_progress(
    class_id: int = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """获取投票和评分进度"""
    # 获取系统设置以确定当前比赛
    settings_result = await db.execute(
        select(SystemSettings).where(SystemSettings.class_id == class_id)
    )
    settings = settings_result.scalar_one_or_none()
    
    contest = None
    if settings and settings.contest_id:
        contest_result = await db.execute(
            select(Contest).where(Contest.id == settings.contest_id)
        )
        contest = contest_result.scalar_one_or_none()
        
    if not contest:
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
    
    # 使用 SystemSettings 中的投票开启标志
    pre_voting_enabled = False
    post_voting_enabled = False
    judge_scoring_enabled = False
    
    if settings:
        pre_voting_enabled = settings.pre_voting_enabled or False
        post_voting_enabled = settings.post_voting_enabled or False
        judge_scoring_enabled = settings.judge_scoring_enabled or False
    
    # 计算观众总数（排除辩手和评委）
    audience_count_res = await db.execute(
        select(func.count(User.id))
        .where(User.class_id == class_id)
        .where(User.role == UserRole.audience)
    )
    total_audience = audience_count_res.scalar() or 0
    
    pre_votes_res = await db.execute(
        select(func.count(VoteRecord.id))
        .where(VoteRecord.contest_id == contest_id)
        .where(VoteRecord.vote_phase == "pre_debate")
    )
    pre_submitted = pre_votes_res.scalar() or 0
    
    post_votes_res = await db.execute(
        select(func.count(VoteRecord.id))
        .where(VoteRecord.contest_id == contest_id)
        .where(VoteRecord.vote_phase == "post_debate")
    )
    post_submitted = post_votes_res.scalar() or 0
    
    judge_count_res = await db.execute(
        select(func.count(TeacherClass.teacher_id))
        .where(TeacherClass.class_id == class_id)
    )
    total_judges = judge_count_res.scalar() or 0
    
    # 修改：计算评委评分进度（需要所有辩手都被评分）
    # 1. 获取辩手总数
    debaters_count_res = await db.execute(
        select(func.count(User.id))
        .where(User.class_id == class_id)
        .where(User.team_side.isnot(None))
        .where(User.debater_position.isnot(None))
    )
    total_debaters = debaters_count_res.scalar() or 0
    
    # 2. 统计每个评委的已评分数量
    completed_judges_count = 0
    if total_debaters > 0:
        judge_scores_res = await db.execute(
            select(JudgeScore.judge_id, func.count(JudgeScore.id))
            .where(JudgeScore.contest_id == contest_id)
            .group_by(JudgeScore.judge_id)
        )
        for _, count in judge_scores_res.all():
            if count >= total_debaters:
                completed_judges_count += 1
    
    return {
        "voting_enabled": {
            "pre_voting": pre_voting_enabled,
            "post_voting": post_voting_enabled,
            "judge_scoring": judge_scoring_enabled
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
            "submitted": completed_judges_count,
            "percentage": int(completed_judges_count / total_judges * 100) if total_judges > 0 else 0
        }
    }


@router.post("/debate/reveal-results")
async def reveal_debate_results(
    class_id: int = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """揭晓比赛结果"""
    try:
        # 获取系统设置
        result = await db.execute(select(SystemSettings).where(SystemSettings.class_id == class_id))
        settings = result.scalar_one_or_none()

        contest = None
        if settings and settings.contest_id:
            contest_result = await db.execute(
                select(Contest).where(Contest.id == settings.contest_id)
            )
            contest = contest_result.scalar_one_or_none()
            
        if not contest:
            # 获取最新比赛
            contest_result = await db.execute(
                select(Contest)
                .where(Contest.class_id == class_id)
                .order_by(Contest.created_at.desc())
                .limit(1)
            )
            contest = contest_result.scalar_one_or_none()
        
        if settings:
            settings.current_stage = "RESULTS_REVEALED"
            settings.update_time = int(time.time() * 1000)
            await db.commit()
            
            # 广播状态更新
            await manager.broadcast_to_class(class_id, {
                "type": "STATE_UPDATE",
                "data": {
                    "current_stage": "RESULTS_REVEALED"
                }
            })
            
            # 尝试获取和广播比赛结果
            try:
                from app.services.calculation import get_calculation_service
                calc_service = get_calculation_service(db)
                contest_result_data = await calc_service.calculate_contest_result(contest.id)
                
                # 准备结果数据
                results_data = {
                    "contest_id": contest_result_data.contest_id,
                    "winning_team": contest_result_data.winning_team,
                    "pro_team_swing": contest_result_data.pro_team_swing,
                    "con_team_swing": contest_result_data.con_team_swing,
                    "total_votes_cast": contest_result_data.total_votes_cast,
                    "debater_rankings": [
                        {
                            "debater_id": ranking.debater_id,
                            "debater_name": ranking.debater_name,
                            "team_side": ranking.team_side,
                            "final_score": ranking.final_score,
                            "rank": ranking.rank
                        }
                        for ranking in contest_result_data.debater_rankings
                    ]
                }
                
                # 广播结果揭晓数据
                await manager.broadcast_to_class(class_id, {
                    "type": "results_reveal",
                    "data": {
                        "results": results_data
                    }
                })
            except Exception as e:
                # 如果计算结果失败，记录错误但不阻止状态更新
                print(f"计算比赛结果失败: {str(e)}")
                import traceback
                traceback.print_exc()
            
        return {"message": "Results revealed"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"揭晓结果失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"揭晓结果失败: {str(e)}")


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
    
    # 允许设置为None以移除角色
    user.team_side = team_side
    user.debater_position = debater_position
    
    # 严格角色区分：
    # 如果分配了位置，强制角色为 'student' (辩手)
    if team_side and debater_position:
        user.role = UserRole.student
    # 如果移除了位置，且当前角色是 student，可以考虑转为 audience
    # 但为了安全，我们只在分配时强制转为 student
        
    await db.commit()
    return {"message": "Role updated"}


@router.post("/debate/reset")
async def reset_debate_system(
    class_id: int = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """重置辩论系统到初始状态"""
    try:
        # 1. 获取该班级的所有比赛
        contests_result = await db.execute(
            select(Contest).where(Contest.class_id == class_id)
        )
        contests = contests_result.scalars().all()
        contest_ids = [c.id for c in contests]
        # 3. 不删除历史数据，仅重置系统状态和当前场次关联
        # 这样可以保留历史记录，同时“进入一个新的场次”
        
        # 4. 重置该班级内所有用户的辩手角色 (释放辩手以便下一场分配)
        # 获取该班级的所有学生用户
        users_result = await db.execute(
            select(User)
            .where(User.class_id == class_id)
            .where(User.role == UserRole.student)
        )
        students = users_result.scalars().all()
        
        for student in students:
            # 清除辩手角色和队伍关联
            student.team_side = None
            student.debater_position = None
            # 注意：不修改 student.role，保持为 student
            # 如果需要也可以在这里重置 role，但通常保持 student 即可
            
        print(f"已重置 {len(students)} 名学生的辩手状态")
        
        # 5. 广播更详细的重置消息，强制前端刷新
        broadcast_data = {
            "type": "debate_update", # 使用标准 update 消息
            "data": {
                "stage": "IDLE",
                "contest": None, # 明确告知没有比赛
                "class_id": class_id,
                "voting_enabled": {
                    "pre_voting": False,
                    "post_voting": False,
                    "judge_scoring": False
                },
                "results_revealed": False,
                "progress": {},
                "update_time": settings.update_time
            }
        }
        
        await manager.broadcast_to_class(class_id, broadcast_data)
        
        await db.commit()
        print(f"事务已提交")
        
        # 7. 广播系统重置消息
        try:
            await manager.broadcast_to_class(class_id, {
                "type": "STATE_UPDATE",
                "data": {
                    "current_stage": "IDLE",
                    "update_time": settings.update_time
                }
            })
            print(f"已广播重置消息")
        except Exception as broadcast_error:
            print(f"广播消息失败（非致命错误）: {str(broadcast_error)}")
        
        return {"message": "系统已重置到初始状态"}
    except Exception as e:
        await db.rollback()
        print(f"重置系统失败: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"重置系统失败: {str(e)}")


@router.get("/debate/results/{contest_id}")
async def get_debate_results(
    contest_id: int,
    db: AsyncSession = Depends(get_db)
):
    """获取辩论结果（计算但不揭晓）"""
    from app.services.calculation import get_calculation_service
    
    calc_service = get_calculation_service(db)
    contest_result = await calc_service.calculate_contest_result(contest_id)
    
    return {
        "contest_id": contest_result.contest_id,
        "winning_team": contest_result.winning_team,
        "pro_team_swing": contest_result.pro_team_swing,
        "con_team_swing": contest_result.con_team_swing,
        "total_votes_cast": contest_result.total_votes_cast,
        "debater_rankings": [
            {
                "debater_id": ranking.debater_id,
                "debater_name": ranking.debater_name,
                "team_side": ranking.team_side,
                "final_score": ranking.final_score,
                "logical_reasoning_avg": ranking.logical_reasoning_avg,
                "debate_skills_avg": ranking.debate_skills_avg,
                "rank": ranking.rank
            }
            for ranking in contest_result.debater_rankings
        ],
        "vote_analysis": [
            {
                "team_side": analysis.team_side,
                "team_name": analysis.team_name,
                "pre_debate_votes": analysis.pre_debate_votes,
                "post_debate_votes": analysis.post_debate_votes,
                "swing_vote": analysis.swing_vote,
                "vote_percentage_change": analysis.vote_percentage_change
            }
            for analysis in contest_result.vote_analysis
        ]
    }