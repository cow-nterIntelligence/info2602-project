from datetime import datetime
from sqlmodel import Field, SQLModel
from typing import Optional


class Challenge(SQLModel, table=True):
    """Represents a challenge between two users"""
    id: Optional[int] = Field(default=None, primary_key=True)
    challenger_id: int = Field(index=True, foreign_key="user.id")
    opponent_id: int = Field(index=True, foreign_key="user.id")
    day: str = Field(index=True)  # Date of the puzzle (YYYY-MM-DD)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Status of game
    status: str = Field(default="pending", index=True)
    
    # Results (null til both players finish or give up)
    challenger_result: Optional[str] = None  # 'solved', 'gave_up', or null if not done
    opponent_result: Optional[str] = None
    
    # number of guesses taken
    challenger_guesses: Optional[int] = None
    opponent_guesses: Optional[int] = None
    
    completed_at: Optional[datetime] = None
