from datetime import datetime
from pydantic import BaseModel
from app.models.score_record import ScorePhase


class ScoreSubmit(BaseModel):
    target_team_id: int
    phase: ScorePhase
    score_details: dict
    total_score: float


class ScoreResponse(BaseModel):
    id: int
    class_id: int
    scorer_id: int
    target_team_id: int
    phase: ScorePhase
    score_details: dict
    total_score: float
    created_at: datetime
    
    class Config:
        from_attributes = True
