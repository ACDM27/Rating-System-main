from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User, UserRole
from app.models.contest import Contest
from app.models.vote_record import VoteRecord
from app.models.system_settings import SystemSettings, SystemStage
from app.schemas.vote import VoteSubmission, VoteResponse, VoteStats
from app.services.auth import get_current_user

router = APIRouter(prefix="/vote", tags=["投票"])


@router.post("/submit", response_model=VoteResponse)
async def submit_vote(
    vote_data: VoteSubmission,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """提交投票"""
    
    # 验证用户角色
    if current_user.role not in [UserRole.audience, UserRole.student]:
        raise HTTPException(status_code=403, detail="只有观众可以投票")
    
    # 验证比赛存在
    result = await db.execute(select(Contest).where(Contest.id == vote_data.contest_id))
    contest = result.scalar_one_or_none()
    if not contest:
        raise HTTPException(status_code=404, detail="比赛不存在")
    
    # 验证用户有权限访问该班级的比赛
    if current_user.class_id != contest.class_id:
        raise HTTPException(status_code=403, detail="无权访问该比赛")
    
    # 检查系统状态是否允许投票
    result = await db.execute(
        select(SystemSettings).where(SystemSettings.class_id == contest.class_id)
    )
    system_settings = result.scalar_one_or_none()
    if not system_settings:
        raise HTTPException(status_code=404, detail="系统设置不存在")
    
    # 验证投票阶段
    if vote_data.vote_phase == "pre_debate":
        if not system_settings.pre_voting_enabled:
            raise HTTPException(status_code=400, detail="赛前投票未开启")
    elif vote_data.vote_phase == "post_debate":
        if not system_settings.post_voting_enabled:
            raise HTTPException(status_code=400, detail="赛后投票未开启")
    else:
        raise HTTPException(status_code=400, detail="无效的投票阶段")
    
    # 检查是否已经投过票
    result = await db.execute(
        select(VoteRecord)
        .where(VoteRecord.contest_id == vote_data.contest_id)
        .where(VoteRecord.voter_id == current_user.id)
        .where(VoteRecord.vote_phase == vote_data.vote_phase)
    )
    existing_vote = result.scalar_one_or_none()
    if existing_vote:
        raise HTTPException(status_code=400, detail=f"您已经在{vote_data.vote_phase}阶段投过票了")
    
    # 创建投票记录
    vote_record = VoteRecord(
        contest_id=vote_data.contest_id,
        voter_id=current_user.id,
        team_side=vote_data.team_side,
        vote_phase=vote_data.vote_phase
    )
    
    db.add(vote_record)
    await db.commit()
    await db.refresh(vote_record)
    
    return VoteResponse(
        id=vote_record.id,
        contest_id=vote_record.contest_id,
        voter_id=vote_record.voter_id,
        team_side=vote_record.team_side,
        vote_phase=vote_record.vote_phase,
        created_at=vote_record.created_at
    )


@router.get("/stats/{contest_id}", response_model=VoteStats)
async def get_vote_stats(
    contest_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取投票统计（仅管理员可见详细数据）"""
    
    # 验证比赛存在
    result = await db.execute(select(Contest).where(Contest.id == contest_id))
    contest = result.scalar_one_or_none()
    if not contest:
        raise HTTPException(status_code=404, detail="比赛不存在")
    
    # 验证权限
    if current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="只有管理员可以查看详细投票统计")
    
    # 统计各阶段投票数
    result = await db.execute(
        select(
            VoteRecord.team_side,
            VoteRecord.vote_phase,
            func.count(VoteRecord.id).label('count')
        )
        .where(VoteRecord.contest_id == contest_id)
        .group_by(VoteRecord.team_side, VoteRecord.vote_phase)
    )
    
    vote_counts = result.all()
    
    # 初始化统计数据
    stats = {
        'pro_pre_votes': 0,
        'con_pre_votes': 0,
        'pro_post_votes': 0,
        'con_post_votes': 0
    }
    
    # 填充统计数据
    for team_side, vote_phase, count in vote_counts:
        key = f"{team_side}_{vote_phase}_votes"
        if key in stats:
            stats[key] = count
    
    # 计算跑票值
    pro_swing = stats['pro_post_votes'] - stats['pro_pre_votes']
    con_swing = stats['con_post_votes'] - stats['con_pre_votes']
    
    # 计算总投票人数
    result = await db.execute(
        select(func.count(func.distinct(VoteRecord.voter_id)))
        .where(VoteRecord.contest_id == contest_id)
    )
    total_voters = result.scalar() or 0
    
    return VoteStats(
        pro_pre_votes=stats['pro_pre_votes'],
        con_pre_votes=stats['con_pre_votes'],
        pro_post_votes=stats['pro_post_votes'],
        con_post_votes=stats['con_post_votes'],
        pro_swing_vote=pro_swing,
        con_swing_vote=con_swing,
        total_voters=total_voters
    )


@router.get("/my-votes/{contest_id}")
async def get_my_votes(
    contest_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取当前用户的投票记录"""
    
    # 验证比赛存在
    result = await db.execute(select(Contest).where(Contest.id == contest_id))
    contest = result.scalar_one_or_none()
    if not contest:
        raise HTTPException(status_code=404, detail="比赛不存在")
    
    # 验证用户有权限访问该班级的比赛
    if current_user.class_id != contest.class_id:
        raise HTTPException(status_code=403, detail="无权访问该比赛")
    
    # 获取用户投票记录
    result = await db.execute(
        select(VoteRecord)
        .where(VoteRecord.contest_id == contest_id)
        .where(VoteRecord.voter_id == current_user.id)
    )
    votes = result.scalars().all()
    
    vote_status = {
        'pre_debate_voted': False,
        'post_debate_voted': False,
        'pre_debate_team': None,
        'post_debate_team': None
    }
    
    for vote in votes:
        if vote.vote_phase == 'pre_debate':
            vote_status['pre_debate_voted'] = True
            vote_status['pre_debate_team'] = vote.team_side
        elif vote.vote_phase == 'post_debate':
            vote_status['post_debate_voted'] = True
            vote_status['post_debate_team'] = vote.team_side
    
    return vote_status


@router.get("/progress/{contest_id}")
async def get_vote_progress(
    contest_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """获取投票进度（大屏显示用，不显示具体票数分布）"""
    
    # 验证比赛存在
    result = await db.execute(select(Contest).where(Contest.id == contest_id))
    contest = result.scalar_one_or_none()
    if not contest:
        raise HTTPException(status_code=404, detail="比赛不存在")
    
    # 统计总投票人数（不显示具体分布）
    result = await db.execute(
        select(func.count(func.distinct(VoteRecord.voter_id)))
        .where(VoteRecord.contest_id == contest_id)
    )
    total_voters = result.scalar() or 0
    
    # 统计各阶段投票人数
    result = await db.execute(
        select(
            VoteRecord.vote_phase,
            func.count(func.distinct(VoteRecord.voter_id)).label('count')
        )
        .where(VoteRecord.contest_id == contest_id)
        .group_by(VoteRecord.vote_phase)
    )
    
    phase_counts = {row.vote_phase: row.count for row in result.all()}
    
    return {
        'total_voters': total_voters,
        'pre_debate_voters': phase_counts.get('pre_debate', 0),
        'post_debate_voters': phase_counts.get('post_debate', 0),
        'contest_topic': contest.topic,
        'pro_team_name': contest.pro_team_name,
        'con_team_name': contest.con_team_name
    }