from datetime import datetime
from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Contest(Base):
    """辩论比赛配置"""
    __tablename__ = "contests"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"), nullable=False)
    topic: Mapped[str] = mapped_column(String(500), nullable=False)
    pro_topic: Mapped[str] = mapped_column(String(500), nullable=True)
    con_topic: Mapped[str] = mapped_column(String(500), nullable=True)
    pro_team_name: Mapped[str] = mapped_column(String(100), nullable=False)
    con_team_name: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # 关系
    class_ = relationship("Class", back_populates="contests")
    vote_records = relationship("VoteRecord", back_populates="contest", cascade="all, delete-orphan")
    judge_scores = relationship("JudgeScore", back_populates="contest", cascade="all, delete-orphan")