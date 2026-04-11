from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class GameGuess(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    day: str = Field(index=True)  # Format: "YYYY-MM-DD"
    guess: str
    bulls: int
    cows: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)