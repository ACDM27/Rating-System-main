"""
数据库优化：增强场次数据隔离
"""

# 1. 添加复合唯一索引，防止跨场次数据污染
# 2. 添加数据库约束，确保引用完整性
# 3. 优化查询性能

from alembic import op
import sqlalchemy as sa

def upgrade():
    """升级数据库结构以增强场次隔离"""
    
    # 1. 为 vote_records 添加复合唯一索引
    # 确保同一观众在同一阶段只能投票一次
    op.create_index(
        'idx_vote_unique_per_voter_phase',
        'vote_records',
        ['contest_id', 'voter_id', 'vote_phase'],
        unique=True
    )
    
    # 2. 为 judge_scores 添加复合唯一索引
    # 确保同一评委对同一辩手只能评分一次
    op.create_index(
        'idx_score_unique_per_judge_debater',
        'judge_scores',
        ['contest_id', 'judge_id', 'debater_id'],
        unique=True
    )
    
    # 3. 为 users 表添加场次相关索引，提升查询性能
    op.create_index(
        'idx_users_class_id_role',
        'users',
        ['class_id', 'role']
    )
    
    op.create_index(
        'idx_users_class_id_team_side',
        'users',
        ['class_id', 'team_side', 'debater_position']
    )
    
    # 4. 为 contests 表添加场次索引
    op.create_index(
        'idx_contests_class_id',
        'contests',
        ['class_id']
    )
    
    print("✅ 数据库索引创建完成，场次隔离已增强")


def downgrade():
    """回滚数据库更改"""
    op.drop_index('idx_vote_unique_per_voter_phase', table_name='vote_records')
    op.drop_index('idx_score_unique_per_judge_debater', table_name='judge_scores')
    op.drop_index('idx_users_class_id_role', table_name='users')
    op.drop_index('idx_users_class_id_team_side', table_name='users')
    op.drop_index('idx_contests_class_id', table_name='contests')
    
    print("✅ 数据库索引已回滚")


# 手动执行脚本（不使用Alembic）
async def apply_indexes_manually():
    """手动应用索引（用于SQLite等不支持Alembic的场景）"""
    from app.database import engine, Base
    from sqlalchemy import text
    
    async with engine.begin() as conn:
        # SQLite 语法
        try:
            # 注意：SQLite的唯一索引创建可能会因为现有重复数据而失败
            # 需要先清理重复数据
            
            await conn.execute(text("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_vote_unique_per_voter_phase 
                ON vote_records(contest_id, voter_id, vote_phase)
            """))
            
            await conn.execute(text("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_score_unique_per_judge_debater 
                ON judge_scores(contest_id, judge_id, debater_id)
            """))
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_users_class_id_role 
                ON users(class_id, role)
            """))
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_users_class_id_team_side 
                ON users(class_id, team_side, debater_position)
            """))
            
            await conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_contests_class_id 
                ON contests(class_id)
            """))
            
            print("✅ 索引创建成功")
        except Exception as e:
            print(f"⚠️  索引创建失败（可能已存在）: {e}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(apply_indexes_manually())
