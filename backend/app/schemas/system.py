from pydantic import BaseModel
from app.models.system_settings import SystemStage


class SystemStateResponse(BaseModel):
    class_id: int
    current_stage: SystemStage
    current_team_id: int | None
    current_team_name: str | None = None
    current_team_topic: str | None = None
    snatch_slots_remaining: int
    snatch_start_time: int | None = None  # 毫秒时间戳
    countdown: int | None = None  # 当前倒计时剩余秒数
    teacher_avg_score: float | None = None  # 教师评分平均分
    student_avg_score: float | None = None  # 学生评分平均分
    teacher_scoring_completed: bool = False  # 教师评分是否完成
    student_scoring_completed: bool = False  # 学生评分是否完成
    update_time: int | None = None  # 状态更新时间（毫秒时间戳）
    
    class Config:
        from_attributes = True


class StageSetRequest(BaseModel):
    stage: SystemStage
    target_team_id: int | None = None


class ScoreProgressResponse(BaseModel):
    submitted_count: int
    total_count: int
    not_submitted: list[dict]  # [{"id": 1, "display_name": "Team01"}, ...]
