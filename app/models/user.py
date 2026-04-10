from datetime import datetime
from sqlmodel import Field, SQLModel
from typing import Optional
from pydantic import EmailStr


class UserBase(SQLModel,):
    username: str = Field(index=True, unique=True)
    email: EmailStr = Field(index=True, unique=True)
    password: str
    role:str = ""

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

class GameGuess(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True, foreign_key="user.id")
    day: str = Field(index=True)  # Format: "YYYY-MM-DD"
    guess: str
    bulls: int
    cows: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)

