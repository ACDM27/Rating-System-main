import enum
import time
from sqlalchemy import ForeignKey, Enum, Integer, BigInteger, Text, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def get_current_timestamp_ms():
    """获取当前毫秒时间戳"""
    return int(time.time() * 1000)


class SystemStage(str, enum.Enum):
    IDLE = "IDLE"  # 未开始
    PRESENTATION = "PRESENTATION"  # 答辩中（保持兼容性）
    QNA_SNATCH = "QNA_SNATCH"  # 提问环节（保持兼容性）
    QNA_INPUT = "QNA_INPUT"  # 提问输入环节（保持兼容性）
    SCORING_TEACHER = "SCORING_TEACHER"  # 教师评分中（保持兼容性）
    SCORING_STUDENT = "SCORING_STUDENT"  # 学生互评中（保持兼容性）
    FINISHED = "FINISHED"  # 当前团队结束（保持兼容性）
    
    # 新的辩论赛阶段
    PRE_VOTING = "PRE_VOTING"  # 赛前投票
    DEBATE_IN_PROGRESS = "DEBATE_IN_PROGRESS"  # 辩论进行中
    POST_VOTING = "POST_VOTING"  # 赛后投票
    JUDGE_SCORING = "JUDGE_SCORING"  # 评委评分
    RESULTS_SEALED = "RESULTS_SEALED"  # 结果封存
    RESULTS_REVEALED = "RESULTS_REVEALED"  # 结果揭晓


class SystemSettings(Base):
    """系统设置 - 每个班级有独立的系统状态"""
    __tablename__ = "system_settings"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"), nullable=False, unique=True)
    current_stage: Mapped[SystemStage] = mapped_column(Enum(SystemStage), nullable=False, default=SystemStage.IDLE)
    current_team_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    snatch_slots_remaining: Mapped[int] = mapped_column(Integer, nullable=False, default=3)
    snatch_start_time: Mapped[int | None] = mapped_column(BigInteger, nullable=True)  # 毫秒时间戳
    update_time: Mapped[int] = mapped_column(BigInteger, nullable=False, default=get_current_timestamp_ms, onupdate=get_current_timestamp_ms)  # 更新时间（毫秒时间戳）
    snatch_rules: Mapped[str | None] = mapped_column(Text, nullable=True, default="• 每轮答辩共 3 个提问名额，先到先得\n• 倒计时结束后，剩余名额将随机分配\n• 提问质量将由评委评分，计入团队总成绩\n• 请认真思考后提出有价值的问题")  # 提问规则说明
    
    # 辩论赛专用字段
    contest_id: Mapped[int | None] = mapped_column(ForeignKey("contests.id"), nullable=True)
    pre_voting_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    post_voting_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    judge_scoring_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    results_revealed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # 关系
    class_ = relationship("Class", back_populates="system_settings")
