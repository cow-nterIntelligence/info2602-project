from sqlmodel import Session, select
from datetime import date
from typing import List, Optional
from app.models.game_guess import GameGuess

def get_user_guesses_today(session: Session, user_id: int) -> List[GameGuess]:
    """Get all guesses made by user today"""
    return session.exec(
        select(GameGuess)
        .where(GameGuess.user_id == user_id)
        .where(GameGuess.puzzle_date == date.today())
        .order_by(GameGuess.created_at)
    ).all()

def has_user_won_today(session: Session, user_id: int) -> bool:
    """Check if user already won today's puzzle"""
    winning_guess = session.exec(
        select(GameGuess)
        .where(GameGuess.user_id == user_id)
        .where(GameGuess.puzzle_date == date.today())
        .where(GameGuess.is_win == True)
    ).first()
    return winning_guess is not None

def create_guess(
    session: Session, 
    user_id: int, 
    guess: str, 
    bulls: int, 
    cows: int,
    is_win: bool
) -> GameGuess:
    """Record a user's guess"""
    attempt = GameGuess(
        user_id=user_id,
        puzzle_date=date.today(),
        guess=guess,
        bulls=bulls,
        cows=cows,
        is_win=is_win
    )
    session.add(attempt)
    session.commit()
    session.refresh(attempt)
    return attempt

def get_user_history(session: Session, user_id: int) -> List[GameGuess]:
    """Get all past guesses for history page"""
    return session.exec(
        select(GameGuess)
        .where(GameGuess.user_id == user_id)
        .order_by(GameGuess.puzzle_date.desc(), GameGuess.created_at.desc())
    ).all()