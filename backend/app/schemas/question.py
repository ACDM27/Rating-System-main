from datetime import datetime
from pydantic import BaseModel
from app.models.question import QuestionStatus


class QuestionCreate(BaseModel):
    target_team_id: int


class QuestionSubmit(BaseModel):
    question_id: int
    content: str


class QuestionGrade(BaseModel):
    question_id: int
    quality_score: float


class QuestionResponse(BaseModel):
    id: int
    asker_team_id: int
    asker_name: str | None = None
    target_team_id: int
    content: str | None
    quality_score: float | None
    status: QuestionStatus
    created_at: datetime
    
    class Config:
        from_attributes = True
