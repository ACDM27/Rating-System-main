from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Class(Base):
    """班级模型 - 每个工作空间内有多个班级"""
    __tablename__ = "classes"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    workspace_id: Mapped[int] = mapped_column(ForeignKey("workspaces.id"), nullable=False)
    
    # 关系
    workspace = relationship("Workspace", back_populates="classes")
    teacher_associations = relationship("TeacherClass", back_populates="class_", cascade="all, delete-orphan")
    system_settings = relationship("SystemSettings", back_populates="class_", uselist=False, cascade="all, delete-orphan")
    contests = relationship("Contest", back_populates="class_", cascade="all, delete-orphan")
