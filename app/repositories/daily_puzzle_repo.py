from sqlmodel import Session, select
from datetime import date
from app.models.daily_puzzle import DailyPuzzle
from app.services.game_service import generate_secret_number

def get_or_create_today_puzzle(session: Session) -> str:
    """
    Gets today's puzzle or creates a new one if it doesn't exist.
    Same puzzle is returned for ALL users.
    """
    today = date.today()
    
    # Try to get existing puzzle for today
    puzzle = session.exec(
        select(DailyPuzzle).where(DailyPuzzle.puzzle_date == today)
    ).first()
    
    if puzzle:
        return puzzle.secret_number
    
    # Create new puzzle for today
    new_puzzle = DailyPuzzle(
        puzzle_date=today,
        secret_number=generate_secret_number()
    )
    session.add(new_puzzle)
    session.commit()
    session.refresh(new_puzzle)
    
    return new_puzzle.secret_number