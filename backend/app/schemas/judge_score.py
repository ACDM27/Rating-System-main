from datetime import datetime
from pydantic import BaseModel, validator
from typing import List


class JudgeScoreSubmission(BaseModel):
    contest_id: int
    debater_id: int
    language_expression: float
    logical_reasoning: float
    debate_skills: float
    quick_response: float
    overall_awareness: float
    general_impression: float
    
    @validator('language_expression', 'logical_reasoning', 'debate_skills')
    def validate_20_point_scores(cls, v):
        if not 0 <= v <= 20:
            raise ValueError('Score must be between 0 and 20')
        return v
    
    @validator('quick_response', 'overall_awareness')
    def validate_15_point_scores(cls, v):
        if not 0 <= v <= 15:
            raise ValueError('Score must be between 0 and 15')
        return v
    
    @validator('general_impression')
    def validate_10_point_score(cls, v):
        if not 0 <= v <= 10:
            raise ValueError('Score must be between 0 and 10')
        return v


class JudgeScoreResponse(BaseModel):
    id: int
    contest_id: int
    judge_id: int
    debater_id: int
    language_expression: float
    logical_reasoning: float
    debate_skills: float
    quick_response: float
    overall_awareness: float
    general_impression: float
    total_score: float
    created_at: datetime
    
    class Config:
        from_attributes = True


class DebaterRanking(BaseModel):
    debater_id: int
    debater_name: str
    team_side: str
    final_score: float  # Average of all judge scores (2 decimal places)
    logical_reasoning_avg: float  # First tiebreaker
    debate_skills_avg: float      # Second tiebreaker
    rank: int


class TeamVoteResult(BaseModel):
    team_side: str
    team_name: str
    pre_debate_votes: int
    post_debate_votes: int
    swing_vote: int  # post - pre
    vote_percentage_change: float


class ContestResult(BaseModel):
    contest_id: int
    winning_team: str  # "pro", "con", or "tie"
    pro_team_swing: int
    con_team_swing: int
    total_votes_cast: int
    debater_rankings: List[DebaterRanking]
    vote_analysis: List[TeamVoteResult]