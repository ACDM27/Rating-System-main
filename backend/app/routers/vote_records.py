from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole
from app.models.contest import Contest
from app.models.vote_record import VoteRecord
from app.models.judge_score import JudgeScore
from app.services.auth import get_current_user

router = APIRouter(prefix="/api", tags=["记录查询"])


@router.get("/vote/records")
async def get_vote_records(
    contest_id: int = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取投票记录详情（管理员查看）"""
    # 验证权限
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="无权访问")
    
    # 获取比赛
    contest_result = await db.execute(select(Contest).where(Contest.id == contest_id))
    contest = contest_result.scalar_one_or_none()
    if not contest:
        raise HTTPException(status_code=404, detail="比赛不存在")
    
    # 获取投票记录并关联用户信息
    result = await db.execute(
        select(VoteRecord, User)
        .join(User, User.id == VoteRecord.voter_id)
        .where(VoteRecord.contest_id == contest_id)
        .order_by(VoteRecord.created_at.desc())
    )
    records = result.all()
    
    return [
        {
            "id": vote.id,
            "voter_id": vote.voter_id,
            "voter_name": user.display_name or user.username,
            "team_side": vote.team_side,
            "vote_phase": vote.vote_phase,
            "created_at": vote.created_at.isoformat()
        }
        for vote, user in records
    ]


@router.get("/judge/scores")
async def get_judge_scores(
    contest_id: int = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取评委评分记录（管理员查看）"""
    # 验证权限
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="无权访问")
    
    # 获取比赛
    contest_result = await db.execute(select(Contest).where(Contest.id == contest_id))
    contest = contest_result.scalar_one_or_none()
    if not contest:
        raise HTTPException(status_code=404, detail="比赛不存在")
    
    # 获取评分记录并关联评委和辩手信息
    result = await db.execute(
        select(JudgeScore, User.alias('judge'), User.alias('debater'))
        .join(User.alias('judge'), User.alias('judge').id == JudgeScore.judge_id)
        .join(User.alias('debater'), User.alias('debater').id == JudgeScore.debater_id)
        .where(JudgeScore.contest_id == contest_id)
        .order_by(JudgeScore.created_at.desc())
    )
    
    # 简化查询
    scores_result = await db.execute(
        select(JudgeScore).where(JudgeScore.contest_id == contest_id)
        .order_by(JudgeScore.created_at.desc())
    )
    scores = scores_result.scalars().all()
    
    # 获取关联的用户信息
    records = []
    for score in scores:
        # 获取评委信息
        judge_result = await db.execute(select(User).where(User.id == score.judge_id))
        judge = judge_result.scalar_one_or_none()
        
        # 获取辩手信息
        debater_result = await db.execute(select(User).where(User.id == score.debater_id))
        debater = debater_result.scalar_one_or_none()
        
        if judge and debater:
            records.append({
                "id": score.id,
                "judge_id": score.judge_id,
                "judge_name": judge.display_name or judge.username,
                "debater_id": score.debater_id,
                "debater_name": debater.display_name or debater.username,
                "team_side": debater.team_side,
                "logical_reasoning": score.logical_reasoning,
                "debate_skills": score.debate_skills,
                "created_at": score.created_at.isoformat()
            })
    
    return records
