from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime

class Guess(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    puzzle_date: str
    guess: str  # e.g., "1234" or empty for giveup
    bulls: int
    cows: int
    action: str = Field(default="guess")  # "guess" or "giveup"
    created_at: datetime = Field(default_factory=datetime.utcnow)