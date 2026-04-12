from datetime import datetime
from sqlmodel import Field, SQLModel
from typing import Optional


class Friend(SQLModel, table=True):
    """Represents a friendship between two users"""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, foreign_key="user.id")
    friend_id: int = Field(index=True, foreign_key="user.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
   
