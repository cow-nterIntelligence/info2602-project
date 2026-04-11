from sqlmodel import Session, select
from app.models.game_guess import Guess
from typing import List
import logging

logger = logging.getLogger(__name__)

class GuessRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, guess_data: Guess) -> Guess:
        try:
            self.db.add(guess_data)
            self.db.commit()
            self.db.refresh(guess_data)
            return guess_data
        except Exception as e:
            logger.error(f"An error occurred while saving guess: {e}")
            self.db.rollback()
            raise

    def get_guesses_by_user_and_date(self, user_id: int, puzzle_date: str) -> List[Guess]:
        return self.db.exec(
            select(Guess)
            .where(Guess.user_id == user_id, Guess.puzzle_date == puzzle_date)
            .order_by(Guess.created_at)
        ).all()

    def has_completed_game(self, user_id: int, puzzle_date: str) -> bool:
        guesses = self.get_guesses_by_user_and_date(user_id, puzzle_date)
        if not guesses:
            return False
        # Check if won or gave up
        return any(g.bulls == 4 for g in guesses) or any(g.action == "giveup" for g in guesses)

    def get_game_status(self, user_id: int, puzzle_date: str) -> str:
        guesses = self.get_guesses_by_user_and_date(user_id, puzzle_date)
        if not guesses:
            return "playing"
        if any(g.bulls == 4 for g in guesses):
            return "won"
        if any(g.action == "giveup" for g in guesses):
            return "gaveup"
        return "playing"