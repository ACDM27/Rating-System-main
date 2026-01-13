from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Workspace(Base):
    """工作空间模型 - 每个管理员对应一个工作空间"""
    __tablename__ = "workspaces"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    admin_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, unique=True)
    
    # 关系
    classes = relationship("Class", back_populates="workspace", cascade="all, delete-orphan")
