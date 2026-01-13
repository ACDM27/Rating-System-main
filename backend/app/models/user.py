import enum
from sqlalchemy import String, Enum, ForeignKey, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(str, enum.Enum):
    admin = "admin"
    teacher = "teacher"  # 保持兼容性
    student = "student"  # 保持兼容性
    judge = "judge"      # 新角色：评委
    audience = "audience"  # 新角色：观众


class User(Base):
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), nullable=False)
    display_name: Mapped[str] = mapped_column(String(100), nullable=False)
    
    # 工作空间关联（所有用户都属于某个工作空间）
    workspace_id: Mapped[int | None] = mapped_column(ForeignKey("workspaces.id"), nullable=True)
    
    # 学生团队的班级关联（学生只属于一个班级）
    class_id: Mapped[int | None] = mapped_column(ForeignKey("classes.id"), nullable=True)
    
    # 答辩状态：标记学生团队是否已完成答辩
    has_presented: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    
    # 学生团队的课题主题
    topic: Mapped[str | None] = mapped_column(String(200), nullable=True)
    
    # 辩论赛专用字段
    debater_position: Mapped[str | None] = mapped_column(String(50), nullable=True)  # "first_speaker", "second_speaker", etc.
    team_side: Mapped[str | None] = mapped_column(String(10), nullable=True)  # "pro" or "con"
    
    # 关系
    class_associations = relationship("TeacherClass", back_populates="teacher", cascade="all, delete-orphan")
