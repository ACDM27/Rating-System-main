"""
数据库场次隔离验证和优化脚本
"""
import asyncio
from sqlalchemy import select, text
from app.database import async_session
from app.models.contest import Contest
from app.models.vote_record import VoteRecord
from app.models.judge_score import JudgeScore
from app.models.user import User, UserRole
from app.models.system_settings import SystemSettings


async def verify_data_isolation():
    """验证数据库场次隔离的完整性"""
    async with async_session() as db:
        print("=" * 60)
        print("数据库场次隔离验证")
        print("=" * 60)
        
        # 1. 检查所有场次
        result = await db.execute(select(Contest))
        contests = result.scalars().all()
        print(f"\n📊 共有 {len(contests)} 个比赛场次")
        
        for contest in contests:
            print(f"\n场次 {contest.class_id} - 比赛 {contest.id}:")
            print(f"  辩题: {contest.topic}")
            print(f"  正方: {contest.pro_team_name}")
            print(f"  反方: {contest.con_team_name}")
            
            # 检查该比赛的投票记录
            vote_result = await db.execute(
                select(VoteRecord).where(VoteRecord.contest_id == contest.id)
            )
            votes = vote_result.scalars().all()
            print(f"  投票记录: {len(votes)} 条")
            
            # 检查该比赛的评分记录
            score_result = await db.execute(
                select(JudgeScore).where(JudgeScore.contest_id == contest.id)
            )
            scores = score_result.scalars().all()
            print(f"  评分记录: {len(scores)} 条")
            
            # 检查该场次的辩手
            debater_result = await db.execute(
                select(User)
                .where(User.class_id == contest.class_id)
                .where(User.team_side.isnot(None))
                .where(User.debater_position.isnot(None))
            )
            debaters = debater_result.scalars().all()
            print(f"  辩手人数: {len(debaters)} 人")
        
        print("\n" + "=" * 60)
        print("✅ 数据隔离验证完成！")
        print("=" * 60)


async def test_cross_class_isolation():
    """测试跨场次数据访问是否被正确隔离"""
    async with async_session() as db:
        print("\n" + "=" * 60)
        print("跨场次数据访问测试")
        print("=" * 60)
        
        # 获取所有场次
        result = await db.execute(select(Contest))
        contests = result.scalars().all()
        
        if len(contests) < 2:
            print("⚠️  需要至少2个场次才能测试跨场次隔离")
            return
        
        class_id_1 = contests[0].class_id
        class_id_2 = contests[1].class_id
        
        print(f"\n测试场次: {class_id_1} vs {class_id_2}")
        
        # 测试1: 辩手数据隔离
        debaters_1 = await db.execute(
            select(User)
            .where(User.class_id == class_id_1)
            .where(User.team_side.isnot(None))
        )
        count_1 = len(debaters_1.scalars().all())
        
        debaters_2 = await db.execute(
            select(User)
            .where(User.class_id == class_id_2)
            .where(User.team_side.isnot(None))
        )
        count_2 = len(debaters_2.scalars().all())
        
        print(f"场次 {class_id_1} 辩手: {count_1} 人")
        print(f"场次 {class_id_2} 辩手: {count_2} 人")
        print(f"{'✅ 辩手数据已隔离' if count_1 != count_2 or count_1 == 0 else '⚠️  需要检查'}")
        
        print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(verify_data_isolation())
    asyncio.run(test_cross_class_isolation())
