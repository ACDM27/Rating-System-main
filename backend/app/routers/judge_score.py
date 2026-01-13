from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List

from app.database import get_db
from app.models.user import User, UserRole
from app.models.contest import Contest
from app.models.judge_score import JudgeScore
from app.models.system_settings import SystemSettings
from app.schemas.judge_score import (
    JudgeScoreSubmission, 
    JudgeScoreResponse, 
    DebaterRanking, 
    TeamVoteResult, 
    ContestResult
)
from app.services.auth import get_current_user

router = APIRouter(prefix="/judge-score", tags=["评委评分"])


@router.post("/submit", response_model=JudgeScoreResponse)
async def submit_judge_score(
    score_data: JudgeScoreSubmission,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """提交评委评分"""
    
    # 验证用户角色
    if current_user.role not in [UserRole.judge, UserRole.teacher]:
        raise HTTPException(status_code=403, detail="只有评委可以评分")
    
    # 验证比赛存在
    result = await db.execute(select(Contest).where(Contest.id == score_data.contest_id))
    contest = result.scalar_one_or_none()
    if not contest:
        raise HTTPException(status_code=404, detail="比赛不存在")
    
    # 验证辩手存在
    result = await db.execute(select(User).where(User.id == score_data.debater_id))
    debater = result.scalar_one_or_none()
    if not debater:
        raise HTTPException(status_code=404, detail="辩手不存在")
    
    # 验证辩手属于该班级
    if debater.class_id != contest.class_id:
        raise HTTPException(status_code=400, detail="辩手不属于该比赛班级")
    
    # 检查系统状态是否允许评分
    result = await db.execute(
        select(SystemSettings).where(SystemSettings.class_id == contest.class_id)
    )
    system_settings = result.scalar_one_or_none()
    if not system_settings or not system_settings.judge_scoring_enabled:
        raise HTTPException(status_code=400, detail="评委评分未开启")
    
    # 检查是否已经评过分
    result = await db.execute(
        select(JudgeScore)
        .where(JudgeScore.contest_id == score_data.contest_id)
        .where(JudgeScore.judge_id == current_user.id)
        .where(JudgeScore.debater_id == score_data.debater_id)
    )
    existing_score = result.scalar_one_or_none()
    if existing_score:
        raise HTTPException(status_code=400, detail="您已经为该辩手评过分了，不能修改")
    
    # 计算总分
    total_score = (
        score_data.language_expression +
        score_data.logical_reasoning +
        score_data.debate_skills +
        score_data.quick_response +
        score_data.overall_awareness +
        score_data.general_impression
    )
    
    # 创建评分记录
    judge_score = JudgeScore(
        contest_id=score_data.contest_id,
        judge_id=current_user.id,
        debater_id=score_data.debater_id,
        language_expression=score_data.language_expression,
        logical_reasoning=score_data.logical_reasoning,
        debate_skills=score_data.debate_skills,
        quick_response=score_data.quick_response,
        overall_awareness=score_data.overall_awareness,
        general_impression=score_data.general_impression,
        total_score=total_score
    )
    
    db.add(judge_score)
    await db.commit()
    await db.refresh(judge_score)
    
    return JudgeScoreResponse(
        id=judge_score.id,
        contest_id=judge_score.contest_id,
        judge_id=judge_score.judge_id,
        debater_id=judge_score.debater_id,
        language_expression=judge_score.language_expression,
        logical_reasoning=judge_score.logical_reasoning,
        debate_skills=judge_score.debate_skills,
        quick_response=judge_score.quick_response,
        overall_awareness=judge_score.overall_awareness,
        general_impression=judge_score.general_impression,
        total_score=judge_score.total_score,
        created_at=judge_score.created_at
    )


@router.get("/my-scores/{contest_id}")
async def get_my_scores(
    contest_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取当前评委的评分记录"""
    
    # 验证用户角色
    if current_user.role not in [UserRole.judge, UserRole.teacher]:
        raise HTTPException(status_code=403, detail="只有评委可以查看评分")
    
    # 验证比赛存在
    result = await db.execute(select(Contest).where(Contest.id == contest_id))
    contest = result.scalar_one_or_none()
    if not contest:
        raise HTTPException(status_code=404, detail="比赛不存在")
    
    # 获取评分记录
    result = await db.execute(
        select(JudgeScore)
        .where(JudgeScore.contest_id == contest_id)
        .where(JudgeScore.judge_id == current_user.id)
    )
    scores = result.scalars().all()
    
    return [
        JudgeScoreResponse(
            id=score.id,
            contest_id=score.contest_id,
            judge_id=score.judge_id,
            debater_id=score.debater_id,
            language_expression=score.language_expression,
            logical_reasoning=score.logical_reasoning,
            debate_skills=score.debate_skills,
            quick_response=score.quick_response,
            overall_awareness=score.overall_awareness,
            general_impression=score.general_impression,
            total_score=score.total_score,
            created_at=score.created_at
        )
        for score in scores
    ]


@router.get("/debater-rankings/{contest_id}", response_model=List[DebaterRanking])
async def get_debater_rankings(
    contest_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取辩手排名（仅管理员可见）"""
    
    # 验证权限
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="只有管理员可以查看排名")
    
    # 验证比赛存在
    result = await db.execute(select(Contest).where(Contest.id == contest_id))
    contest = result.scalar_one_or_none()
    if not contest:
        raise HTTPException(status_code=404, detail="比赛不存在")
    
    # 计算每个辩手的平均分和排名
    result = await db.execute(
        select(
            JudgeScore.debater_id,
            User.display_name,
            User.team_side,
            func.avg(JudgeScore.total_score).label('final_score'),
            func.avg(JudgeScore.logical_reasoning).label('logical_reasoning_avg'),
            func.avg(JudgeScore.debate_skills).label('debate_skills_avg')
        )
        .join(User, User.id == JudgeScore.debater_id)
        .where(JudgeScore.contest_id == contest_id)
        .group_by(JudgeScore.debater_id, User.display_name, User.team_side)
        .order_by(
            func.avg(JudgeScore.total_score).desc(),
            func.avg(JudgeScore.logical_reasoning).desc(),
            func.avg(JudgeScore.debate_skills).desc()
        )
    )
    
    rankings_data = result.all()
    
    # 构建排名列表
    rankings = []
    current_rank = 1
    
    for i, (debater_id, debater_name, team_side, final_score, logical_avg, debate_avg) in enumerate(rankings_data):
        # 处理并列排名
        if i > 0:
            prev_score = rankings_data[i-1][3]  # final_score
            prev_logical = rankings_data[i-1][4]  # logical_reasoning_avg
            prev_debate = rankings_data[i-1][5]  # debate_skills_avg
            
            if (final_score != prev_score or 
                logical_avg != prev_logical or 
                debate_avg != prev_debate):
                current_rank = i + 1
        
        rankings.append(DebaterRanking(
            debater_id=debater_id,
            debater_name=debater_name,
            team_side=team_side or "unknown",
            final_score=round(float(final_score), 2),
            logical_reasoning_avg=round(float(logical_avg), 2),
            debate_skills_avg=round(float(debate_avg), 2),
            rank=current_rank
        ))
    
    return rankings


@router.get("/progress/{contest_id}")
async def get_scoring_progress(
    contest_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取评分进度（管理员可见）"""
    
    # 验证权限
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="只有管理员可以查看进度")
    
    # 验证比赛存在
    result = await db.execute(select(Contest).where(Contest.id == contest_id))
    contest = result.scalar_one_or_none()
    if not contest:
        raise HTTPException(status_code=404, detail="比赛不存在")
    
    # 统计评委总数
    result = await db.execute(
        select(func.count(User.id))
        .where(User.class_id == contest.class_id)
        .where(User.role.in_([UserRole.judge, UserRole.teacher]))
    )
    total_judges = result.scalar() or 0
    
    # 统计辩手总数
    result = await db.execute(
        select(func.count(User.id))
        .where(User.class_id == contest.class_id)
        .where(User.team_side.isnot(None))
    )
    total_debaters = result.scalar() or 0
    
    # 统计已提交评分数
    result = await db.execute(
        select(func.count(JudgeScore.id))
        .where(JudgeScore.contest_id == contest_id)
    )
    submitted_scores = result.scalar() or 0
    
    # 计算预期总评分数（每个评委为每个辩手评分）
    expected_total_scores = total_judges * total_debaters
    
    # 获取未提交评分的评委
    result = await db.execute(
        select(User.id, User.display_name)
        .where(User.class_id == contest.class_id)
        .where(User.role.in_([UserRole.judge, UserRole.teacher]))
    )
    all_judges = result.all()
    
    # 获取已提交评分的评委
    result = await db.execute(
        select(func.distinct(JudgeScore.judge_id))
        .where(JudgeScore.contest_id == contest_id)
    )
    submitted_judge_ids = {row[0] for row in result.all()}
    
    # 找出未提交的评委
    not_submitted_judges = [
        {"id": judge_id, "display_name": display_name}
        for judge_id, display_name in all_judges
        if judge_id not in submitted_judge_ids
    ]
    
    return {
        "total_judges": total_judges,
        "total_debaters": total_debaters,
        "submitted_scores": submitted_scores,
        "expected_total_scores": expected_total_scores,
        "completion_percentage": round((submitted_scores / expected_total_scores * 100) if expected_total_scores > 0 else 0, 1),
        "not_submitted_judges": not_submitted_judges
    }