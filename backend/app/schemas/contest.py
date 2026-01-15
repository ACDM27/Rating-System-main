from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class DebaterInfo(BaseModel):
    name: str
    position: str  # "first_speaker", "second_speaker", etc.


class ContestConfig(BaseModel):
    topic: str
    pro_topic: Optional[str] = None
    con_topic: Optional[str] = None
    pro_team_name: str
    con_team_name: str
    pro_debaters: List[DebaterInfo]
    con_debaters: List[DebaterInfo]


class ContestCreate(BaseModel):
    class_id: int
    topic: str
    pro_topic: Optional[str] = None
    con_topic: Optional[str] = None
    pro_team_name: str
    con_team_name: str


class ContestResponse(BaseModel):
    id: int
    class_id: int
    topic: str
    pro_topic: Optional[str] = None
    con_topic: Optional[str] = None
    pro_team_name: str
    con_team_name: str
    created_at: datetime
    
    class Config:
        from_attributes = True