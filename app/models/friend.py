from datetime import datetime
from sqlmodel import Field, SQLModel
from typing import Optional


class Friend(SQLModel, table=True):
    """Represents a friendship/friend request between two users"""
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, foreign_key="user.id")   # requester
    friend_id: int = Field(index=True, foreign_key="user.id") # recipient
    status: str = Field(default="pending", index=True)         # 'pending' or 'accepted'
    created_at: datetime = Field(default_factory=datetime.utcnow)

