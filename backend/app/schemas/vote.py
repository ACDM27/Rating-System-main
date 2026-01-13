from datetime import datetime
from pydantic import BaseModel, validator


class VoteSubmission(BaseModel):
    contest_id: int
    team_side: str  # "pro" or "con"
    vote_phase: str  # "pre_debate" or "post_debate"
    
    @validator('team_side')
    def validate_team_side(cls, v):
        if v not in ['pro', 'con']:
            raise ValueError('team_side must be "pro" or "con"')
        return v
    
    @validator('vote_phase')
    def validate_vote_phase(cls, v):
        if v not in ['pre_debate', 'post_debate']:
            raise ValueError('vote_phase must be "pre_debate" or "post_debate"')
        return v


class VoteResponse(BaseModel):
    id: int
    contest_id: int
    voter_id: int
    team_side: str
    vote_phase: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class VoteStats(BaseModel):
    pro_pre_votes: int
    con_pre_votes: int
    pro_post_votes: int
    con_post_votes: int
    pro_swing_vote: int
    con_swing_vote: int
    total_voters: int