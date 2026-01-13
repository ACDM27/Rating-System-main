from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class TeacherClass(Base):
    """教师-班级关联表 - 教师可以在多个班级担任评委"""
    __tablename__ = "teacher_classes"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    class_id: Mapped[int] = mapped_column(ForeignKey("classes.id"), nullable=False)
    
    # 关系
    teacher = relationship("User", back_populates="class_associations")
    class_ = relationship("Class", back_populates="teacher_associations")
    
    __table_args__ = (
        UniqueConstraint("teacher_id", "class_id", name="uq_teacher_class"),
    )
