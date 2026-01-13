from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class VoteRecord(Base):
    """投票记录"""
    __tablename__ = "vote_records"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    contest_id: Mapped[int] = mapped_column(ForeignKey("contests.id"), nullable=False)
    voter_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    team_side: Mapped[str] = mapped_column(String(10), nullable=False)  # "pro" or "con"
    vote_phase: Mapped[str] = mapped_column(String(20), nullable=False)  # "pre_debate" or "post_debate"
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # 关系
    contest = relationship("Contest", back_populates="vote_records")
    voter = relationship("User", foreign_keys=[voter_id])
    
    __table_args__ = (
        {"sqlite_autoincrement": True},
    )