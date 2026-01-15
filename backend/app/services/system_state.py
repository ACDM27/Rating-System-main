from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional

from app.models.system_settings import SystemSettings, SystemStage
from app.models.user import User

from app.models.contest import Contest
from app.models.vote_record import VoteRecord
from app.models.judge_score import JudgeScore

from app.websocket import manager

async def broadcast_latest_state(db: AsyncSession, class_id: int):
    """获取最新系统状态并广播"""
    # 1. 获取系统设置
    result = await db.execute(select(SystemSettings).where(SystemSettings.class_id == class_id))
    settings = result.scalar_one_or_none()
    
    if not settings:
        return

    # 2. 获取当前团队信息
    team_info = None
    team_name = None
    if settings.current_team_id:
        team_result = await db.execute(select(User).where(User.id == settings.current_team_id))
        team = team_result.scalar_one_or_none()
        if team:
            team_info = {"id": team.id, "name": team.display_name}
            team_name = team.display_name

    # 3. 计算平均分
    teacher_avg_score = None
    # 移除旧的评分逻辑，因为ScoreRecord模型缺失
    # if settings.current_team_id and settings.current_stage in [SystemStage.SCORING_TEACHER, SystemStage.SCORING_STUDENT, SystemStage.FINISHED]:
    #     ...

    student_avg_score = None
    # if settings.current_team_id and settings.current_stage in [SystemStage.SCORING_STUDENT, SystemStage.FINISHED]:
    #     ...

    # 4. 计算评分完成状态
    teacher_scoring_completed = False
    # if settings.current_team_id and settings.current_stage in [SystemStage.SCORING_TEACHER, SystemStage.SCORING_STUDENT, SystemStage.FINISHED]:
    #     ...
        
    student_scoring_completed = False
    # if settings.current_team_id and settings.current_stage in [SystemStage.SCORING_STUDENT, SystemStage.FINISHED]:
    #     ...

    # 5. 广播
    await manager.broadcast_state_update(
        stage=settings.current_stage.value,
        current_team=team_info,
        snatch_remaining=settings.snatch_slots_remaining,
        snatch_start_time=settings.snatch_start_time,
        class_id=class_id,
        teacher_avg_score=teacher_avg_score,
        student_avg_score=student_avg_score,
        teacher_scoring_completed=teacher_scoring_completed,
        student_scoring_completed=student_scoring_completed,
        update_time=settings.update_time
    )

async def update_debate_stage(db: AsyncSession, class_id: int, stage: SystemStage, contest_id: Optional[int] = None) -> bool:
    """
    更新辩论阶段，确保互斥性
    
    Args:
        db: 数据库会话
        class_id: 班级ID
        stage: 新的系统阶段
        contest_id: 比赛ID（可选）
        
    Returns:
        bool: 是否成功更新
    """
    # 获取当前系统设置
    result = await db.execute(select(SystemSettings).where(SystemSettings.class_id == class_id))
    settings = result.scalar_one_or_none()
    
    if not settings:
        # 如果不存在设置，创建新的
        settings = SystemSettings(
            class_id=class_id,
            current_stage=stage,
            contest_id=contest_id
        )
        db.add(settings)
    else:
        # 更新现有设置
        settings.current_stage = stage
        if contest_id:
            settings.contest_id = contest_id
    
    # 根据阶段设置互斥控制
    if stage == SystemStage.PRE_VOTING:
        settings.pre_voting_enabled = True
        settings.post_voting_enabled = False
        settings.judge_scoring_enabled = False
    elif stage == SystemStage.POST_VOTING:
        settings.pre_voting_enabled = False
        settings.post_voting_enabled = True
        settings.judge_scoring_enabled = False
    elif stage == SystemStage.JUDGE_SCORING:
        settings.pre_voting_enabled = False
        settings.post_voting_enabled = False
        settings.judge_scoring_enabled = True
    elif stage == SystemStage.RESULTS_SEALED:
        settings.pre_voting_enabled = False
        settings.post_voting_enabled = False
        settings.judge_scoring_enabled = False
        settings.results_revealed = False
    elif stage == SystemStage.RESULTS_REVEALED:
        settings.pre_voting_enabled = False
        settings.post_voting_enabled = False
        settings.judge_scoring_enabled = False
        settings.results_revealed = True
    else:
        # 其他阶段关闭所有投票和评分
        settings.pre_voting_enabled = False
        settings.post_voting_enabled = False
        settings.judge_scoring_enabled = False
    
    await db.commit()
    
    # 广播状态更新
    await broadcast_debate_state(db, class_id)
    
    return True


async def get_debate_progress(db: AsyncSession, class_id: int) -> Dict[str, Any]:
    """
    获取辩论进度信息（仅管理员可见）
    
    Args:
        db: 数据库会话
        class_id: 班级ID
        
    Returns:
        Dict[str, Any]: 进度信息
    """
    # 获取系统设置
    result = await db.execute(select(SystemSettings).where(SystemSettings.class_id == class_id))
    settings = result.scalar_one_or_none()
    
    if not settings or not settings.contest_id:
        return {"error": "No active contest found"}
    
    contest_id = settings.contest_id
    
    # 统计投票进度
    pre_vote_count = await db.execute(
        select(func.count(VoteRecord.id)).where(
            VoteRecord.contest_id == contest_id,
            VoteRecord.vote_phase == "pre_debate"
        )
    )
    pre_votes = pre_vote_count.scalar() or 0
    
    post_vote_count = await db.execute(
        select(func.count(VoteRecord.id)).where(
            VoteRecord.contest_id == contest_id,
            VoteRecord.vote_phase == "post_debate"
        )
    )
    post_votes = post_vote_count.scalar() or 0
    
    # 统计评委评分进度
    judge_score_count = await db.execute(
        select(func.count(func.distinct(JudgeScore.judge_id))).where(
            JudgeScore.contest_id == contest_id
        )
    )
    judges_submitted = judge_score_count.scalar() or 0
    
    # 统计总评委数
    total_judges_count = await db.execute(
        select(func.count(User.id)).where(
            User.role == "judge"
        )
    )
    total_judges = total_judges_count.scalar() or 0
    
    # 统计总观众数
    total_audience_count = await db.execute(
        select(func.count(User.id)).where(
            User.role == "audience"
        )
    )
    total_audience = total_audience_count.scalar() or 0
    
    return {
        "contest_id": contest_id,
        "current_stage": settings.current_stage.value,
        "pre_voting_progress": {
            "submitted": pre_votes,
            "total": total_audience,
            "percentage": (pre_votes / total_audience * 100) if total_audience > 0 else 0
        },
        "post_voting_progress": {
            "submitted": post_votes,
            "total": total_audience,
            "percentage": (post_votes / total_audience * 100) if total_audience > 0 else 0
        },
        "judge_scoring_progress": {
            "submitted": judges_submitted,
            "total": total_judges,
            "percentage": (judges_submitted / total_judges * 100) if total_judges > 0 else 0
        },
        "voting_enabled": {
            "pre_voting": settings.pre_voting_enabled,
            "post_voting": settings.post_voting_enabled,
            "judge_scoring": settings.judge_scoring_enabled
        },
        "results_revealed": settings.results_revealed
    }


async def broadcast_debate_state(db: AsyncSession, class_id: int):
    """广播辩论状态更新"""
    # 获取系统设置
    result = await db.execute(select(SystemSettings).where(SystemSettings.class_id == class_id))
    settings = result.scalar_one_or_none()
    
    if not settings:
        return
    
    # 获取比赛信息
    contest_info = None
    if settings.contest_id:
        contest_result = await db.execute(select(Contest).where(Contest.id == settings.contest_id))
        contest = contest_result.scalar_one_or_none()
        if contest:
            contest_info = {
                "id": contest.id,
                "topic": contest.topic,
                "pro_team_name": contest.pro_team_name,
                "con_team_name": contest.con_team_name
            }
    
    # 获取进度信息（仅用于管理员）
    progress_info = await get_debate_progress(db, class_id)
    
    # 广播状态更新
    await manager.broadcast_debate_update(
        stage=settings.current_stage.value,
        contest=contest_info,
        class_id=class_id,
        voting_enabled={
            "pre_voting": settings.pre_voting_enabled,
            "post_voting": settings.post_voting_enabled,
            "judge_scoring": settings.judge_scoring_enabled
        },
        results_revealed=settings.results_revealed,
        progress=progress_info,
        update_time=settings.update_time
    )


async def can_reveal_results(db: AsyncSession, class_id: int) -> bool:
    """
    检查是否可以揭晓结果
    
    Args:
        db: 数据库会话
        class_id: 班级ID
        
    Returns:
        bool: 是否可以揭晓结果
    """
    # 获取系统设置
    result = await db.execute(select(SystemSettings).where(SystemSettings.class_id == class_id))
    settings = result.scalar_one_or_none()
    
    if not settings:
        return False
    
    # 检查所有通道是否已关闭
    all_channels_closed = (
        not settings.pre_voting_enabled and
        not settings.post_voting_enabled and
        not settings.judge_scoring_enabled
    )
    
    return all_channels_closed and settings.current_stage == SystemStage.RESULTS_SEALED