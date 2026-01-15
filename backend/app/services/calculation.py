"""
辩论赛计算引擎
处理跑票计算、队伍获胜者确定和辩手排名逻辑
"""
from typing import List, Dict, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from app.models.vote_record import VoteRecord
from app.models.judge_score import JudgeScore
from app.models.user import User
from app.models.contest import Contest


class TeamVoteResult:
    """队伍投票分析结果"""
    def __init__(self, team_side: str, team_name: str, pre_debate_votes: int, 
                 post_debate_votes: int):
        self.team_side = team_side
        self.team_name = team_name
        self.pre_debate_votes = pre_debate_votes
        self.post_debate_votes = post_debate_votes
        self.swing_vote = post_debate_votes - pre_debate_votes
        
        # 计算票数增长率
        if pre_debate_votes > 0:
            self.growth_rate = (self.swing_vote / pre_debate_votes) * 100
        elif self.swing_vote > 0:
            # 赛前0票，赛后有票，增长率为无穷大
            self.growth_rate = float('inf')
        else:
            # 赛前0票，赛后也是0票（或更少），增长率为0
            self.growth_rate = 0.0
            
        self.vote_percentage_change = self.growth_rate


class DebaterRanking:
    """辩手排名结果"""
    def __init__(self, debater_id: int, debater_name: str, team_side: str,
                 final_score: float, logical_reasoning_avg: float, 
                 debate_skills_avg: float, rank: int):
        self.debater_id = debater_id
        self.debater_name = debater_name
        self.team_side = team_side
        self.final_score = final_score
        self.logical_reasoning_avg = logical_reasoning_avg
        self.debate_skills_avg = debate_skills_avg
        self.rank = rank


class ContestResult:
    """比赛结果"""
    def __init__(self, contest_id: int, winning_team: str, pro_team_swing: int,
                 con_team_swing: int, total_votes_cast: int,
                 debater_rankings: List[DebaterRanking],
                 vote_analysis: List[TeamVoteResult]):
        self.contest_id = contest_id
        self.winning_team = winning_team
        self.pro_team_swing = pro_team_swing
        self.con_team_swing = con_team_swing
        self.total_votes_cast = total_votes_cast
        self.debater_rankings = debater_rankings
        self.vote_analysis = vote_analysis


class CalculationService:
    """计算服务类 (异步版)"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def calculate_swing_votes(self, contest_id: int) -> Tuple[TeamVoteResult, TeamVoteResult]:
        """
        计算跑票值
        
        Args:
            contest_id: 比赛ID
            
        Returns:
            Tuple[TeamVoteResult, TeamVoteResult]: 正方和反方的投票结果
        """
        # 获取比赛信息
        result = await self.db.execute(select(Contest).where(Contest.id == contest_id))
        contest = result.scalar_one_or_none()
        
        if not contest:
            raise ValueError(f"Contest with id {contest_id} not found")
        
        # 统计正方投票
        result = await self.db.execute(
            select(func.count(VoteRecord.id)).where(
                VoteRecord.contest_id == contest_id,
                VoteRecord.team_side == "pro",
                VoteRecord.vote_phase == "pre_debate"
            )
        )
        pro_pre_votes = result.scalar() or 0
        
        result = await self.db.execute(
            select(func.count(VoteRecord.id)).where(
                VoteRecord.contest_id == contest_id,
                VoteRecord.team_side == "pro", 
                VoteRecord.vote_phase == "post_debate"
            )
        )
        pro_post_votes = result.scalar() or 0
        
        # 统计反方投票
        result = await self.db.execute(
            select(func.count(VoteRecord.id)).where(
                VoteRecord.contest_id == contest_id,
                VoteRecord.team_side == "con",
                VoteRecord.vote_phase == "pre_debate"
            )
        )
        con_pre_votes = result.scalar() or 0
        
        result = await self.db.execute(
            select(func.count(VoteRecord.id)).where(
                VoteRecord.contest_id == contest_id,
                VoteRecord.team_side == "con",
                VoteRecord.vote_phase == "post_debate"
            )
        )
        con_post_votes = result.scalar() or 0
        
        # 创建投票结果对象
        pro_result = TeamVoteResult("pro", contest.pro_team_name, pro_pre_votes, pro_post_votes)
        con_result = TeamVoteResult("con", contest.con_team_name, con_pre_votes, con_post_votes)
        
        return pro_result, con_result
    
    async def determine_winner(self, contest_id: int) -> str:
        """
        确定队伍获胜者
        规则：
        Round 1: 比较跑票数 (Swing Vote)
        Round 2: 跑票数相同，比较增长率 (Growth Rate)
        Round 3: 增长率相同，比较赛后总票数 (Post Debate Votes)
        """
        pro_result, con_result = await self.calculate_swing_votes(contest_id)
        
        # Round 1: 比较跑票数 (Swing Vote)
        if pro_result.swing_vote > con_result.swing_vote:
            return "pro"
        elif con_result.swing_vote > pro_result.swing_vote:
            return "con"
        else:
            # Round 2: 跑票数相同，比较增长率 (Growth Rate)
            if pro_result.growth_rate > con_result.growth_rate:
                return "pro"
            elif con_result.growth_rate > pro_result.growth_rate:
                return "con"
            else:
                # Round 3: 增长率相同，比较赛后总票数 (Post Debate Votes)
                if pro_result.post_debate_votes > con_result.post_debate_votes:
                    return "pro"
                elif con_result.post_debate_votes > pro_result.post_debate_votes:
                    return "con"
                else:
                    return "tie"
    
    async def get_vote_statistics(self, contest_id: int) -> Dict[str, int]:
        """
        获取投票统计信息
        
        Args:
            contest_id: 比赛ID
            
        Returns:
            Dict[str, int]: 包含各阶段投票统计的字典
        """
        # 统计总投票数
        result = await self.db.execute(
            select(func.count(VoteRecord.id)).where(
                VoteRecord.contest_id == contest_id,
                VoteRecord.vote_phase == "pre_debate"
            )
        )
        total_pre_votes = result.scalar() or 0
        
        result = await self.db.execute(
            select(func.count(VoteRecord.id)).where(
                VoteRecord.contest_id == contest_id,
                VoteRecord.vote_phase == "post_debate"
            )
        )
        total_post_votes = result.scalar() or 0
        
        # 统计各队投票
        pro_result, con_result = await self.calculate_swing_votes(contest_id)
        
        return {
            "total_pre_votes": total_pre_votes,
            "total_post_votes": total_post_votes,
            "pro_pre_votes": pro_result.pre_debate_votes,
            "pro_post_votes": pro_result.post_debate_votes,
            "pro_swing_vote": pro_result.swing_vote,
            "con_pre_votes": con_result.pre_debate_votes,
            "con_post_votes": con_result.post_debate_votes,
            "con_swing_vote": con_result.swing_vote,
            "total_votes_cast": total_pre_votes + total_post_votes
        }

    async def calculate_debater_rankings(self, contest_id: int) -> List[DebaterRanking]:
        """
        计算辩手排名 (异步)
        
        Args:
            contest_id: 比赛ID
            
        Returns:
            List[DebaterRanking]: 按排名排序的辩手列表
        """
        # 获取所有辩手的评分
        stmt = (
            select(
                JudgeScore.debater_id,
                User.display_name.label('debater_name'),
                User.team_side,
                func.avg(JudgeScore.total_score).label('final_score'),
                func.avg(JudgeScore.logical_reasoning).label('logical_reasoning_avg'),
                func.avg(JudgeScore.debate_skills).label('debate_skills_avg')
            )
            .join(User, JudgeScore.debater_id == User.id)
            .where(JudgeScore.contest_id == contest_id)
            .group_by(JudgeScore.debater_id, User.display_name, User.team_side)
        )
        
        result = await self.db.execute(stmt)
        scores_query = result.all()
        
        # 转换为DebaterRanking对象并排序
        debater_data = []
        for score in scores_query:
            debater_data.append({
                'debater_id': score.debater_id,
                'debater_name': score.debater_name,
                'team_side': score.team_side,
                'final_score': round(float(score.final_score), 2),
                'logical_reasoning_avg': round(float(score.logical_reasoning_avg), 2),
                'debate_skills_avg': round(float(score.debate_skills_avg), 2)
            })
        
        # 按照平分决胜规则排序
        # 1. 最终得分（高者在前）
        # 2. 逻辑推理平均分（高者在前）
        # 3. 辩驳能力平均分（高者在前）
        debater_data.sort(key=lambda x: (
            -x['final_score'],  # 负号表示降序
            -x['logical_reasoning_avg'],
            -x['debate_skills_avg']
        ))
        
        # 分配排名（处理并列情况）
        rankings = []
        current_rank = 1
        
        for i, debater in enumerate(debater_data):
            # 检查是否与前一个辩手并列
            if i > 0:
                prev_debater = debater_data[i-1]
                if (debater['final_score'] != prev_debater['final_score'] or
                    debater['logical_reasoning_avg'] != prev_debater['logical_reasoning_avg'] or
                    debater['debate_skills_avg'] != prev_debater['debate_skills_avg']):
                    current_rank = i + 1
            
            ranking = DebaterRanking(
                debater_id=debater['debater_id'],
                debater_name=debater['debater_name'],
                team_side=debater['team_side'],
                final_score=debater['final_score'],
                logical_reasoning_avg=debater['logical_reasoning_avg'],
                debate_skills_avg=debater['debate_skills_avg'],
                rank=current_rank
            )
            rankings.append(ranking)
        
        return rankings
    
    async def calculate_contest_result(self, contest_id: int) -> ContestResult:
        """
        计算完整的比赛结果 (异步)
        
        Args:
            contest_id: 比赛ID
            
        Returns:
            ContestResult: 完整的比赛结果
        """
        # 计算跑票结果
        pro_result, con_result = await self.calculate_swing_votes(contest_id)
        
        # 确定获胜者
        winning_team = await self.determine_winner(contest_id)
        
        # 计算辩手排名
        debater_rankings = await self.calculate_debater_rankings(contest_id)
        
        # 获取投票统计
        vote_stats = await self.get_vote_statistics(contest_id)
        
        return ContestResult(
            contest_id=contest_id,
            winning_team=winning_team,
            pro_team_swing=pro_result.swing_vote,
            con_team_swing=con_result.swing_vote,
            total_votes_cast=vote_stats['total_votes_cast'],
            debater_rankings=debater_rankings,
            vote_analysis=[pro_result, con_result]
        )


def get_calculation_service(db: AsyncSession) -> CalculationService:
    """获取计算服务实例"""
    return CalculationService(db)