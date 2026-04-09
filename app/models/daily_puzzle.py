from sqlmodel import SQLModel, Field
from datetime import date

class DailyPuzzle(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    puzzle_date: date = Field(index=True, unique=True)  
    secret_number: str = Field(max_length=4)  # e.g., "1234"