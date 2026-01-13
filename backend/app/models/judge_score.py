from datetime import datetime
from sqlalchemy import ForeignKey, Float, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class JudgeScore(Base):
    """评委评分记录"""
    __tablename__ = "judge_scores"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    contest_id: Mapped[int] = mapped_column(ForeignKey("contests.id"), nullable=False)
    judge_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    debater_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    
    # 六个评分维度
    language_expression: Mapped[float] = mapped_column(Float, nullable=False)      # /20
    logical_reasoning: Mapped[float] = mapped_column(Float, nullable=False)        # /20
    debate_skills: Mapped[float] = mapped_column(Float, nullable=False)           # /20
    quick_response: Mapped[float] = mapped_column(Float, nullable=False)          # /15
    overall_awareness: Mapped[float] = mapped_column(Float, nullable=False)       # /15
    general_impression: Mapped[float] = mapped_column(Float, nullable=False)      # /10
    
    total_score: Mapped[float] = mapped_column(Float, nullable=False)             # /100
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # 关系
    contest = relationship("Contest", back_populates="judge_scores")
    judge = relationship("User", foreign_keys=[judge_id])
    debater = relationship("User", foreign_keys=[debater_id])
    
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )