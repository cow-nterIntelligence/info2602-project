from sqlmodel import Session, select
from app.models.game_guess import GameGuess
from app.models.user import User
from datetime import date
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class GameRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_guess(self, user_id: int, day: str, guess: str, bulls: int, cows: int) -> GameGuess:
        record = GameGuess(
            user_id=user_id,
            day=day,
            guess=guess,
            bulls=bulls,
            cows=cows,
        )
        try:
            self.db.add(record)
            self.db.commit()
            self.db.refresh(record)
            return record
        except Exception as e:
            logger.error(f"Error saving guess: {e}")
            self.db.rollback()
            raise

    def get_guesses_for_day(self, user_id: int, day: str) -> list[GameGuess]:
        stmt = (
            select(GameGuess)
            .where(GameGuess.user_id == user_id, GameGuess.day == day)
            .order_by(GameGuess.timestamp)
        )
        return self.db.exec(stmt).all()

    def has_solved_today(self, user_id: int, day: str) -> bool:
        guesses = self.get_guesses_for_day(user_id, day)
        return any(g.bulls == 4 for g in guesses)

    def get_all_guesses_by_day(self, user_id: int) -> dict[str, list[GameGuess]]:
        stmt = (
            select(GameGuess)
            .where(GameGuess.user_id == user_id)
            .order_by(GameGuess.day.desc(), GameGuess.timestamp)
        )
        rows = self.db.exec(stmt).all()

        grouped: dict[str, list[GameGuess]] = {}
        for row in rows:
            grouped.setdefault(row.day, []).append(row)
        return grouped

    def get_leaderboard(self, day: Optional[str] = None, limit: int = 20) -> list[dict]:
        if day is None:
            day = date.today().strftime("%Y-%m-%d")

        stmt = (
            select(GameGuess, User.username)
            .join(User, GameGuess.user_id == User.id)
            .where(GameGuess.day == day)
            .order_by(GameGuess.user_id, GameGuess.timestamp)
        )
        rows = self.db.exec(stmt).all()

        user_data: dict[int, dict] = {}
        for guess, username in rows:
            uid = guess.user_id
            if uid not in user_data:
                user_data[uid] = {
                    "username": username,
                    "guess_count": 0,
                    "solved": False,
                    "solve_time": None,
                }
            if not user_data[uid]["solved"]:
                user_data[uid]["guess_count"] += 1
                if guess.bulls == 4:
                    user_data[uid]["solved"] = True
                    user_data[uid]["solve_time"] = guess.timestamp

        solvers = [v for v in user_data.values() if v["solved"]]
        solvers.sort(key=lambda x: (x["guess_count"], x["solve_time"]))

        leaderboard = []
        for rank, entry in enumerate(solvers[:limit], start=1):
            leaderboard.append({
                "rank": rank,
                "username": entry["username"],
                "guess_count": entry["guess_count"],
                "solve_time": entry["solve_time"].strftime("%H:%M:%S"),
            })
        return leaderboard

    def get_player_stats(self, user_id: int) -> dict:
        stmt = (
            select(GameGuess)
            .where(GameGuess.user_id == user_id)
            .order_by(GameGuess.day, GameGuess.timestamp)
        )
        all_guesses = self.db.exec(stmt).all()

        days_played: set[str] = set()
        days_won: set[str] = set()
        guesses_per_win: list[int] = []
        day_guess_count: dict[str, int] = {}
        day_solved: dict[str, bool] = {}

        for g in all_guesses:
            days_played.add(g.day)
            day_guess_count.setdefault(g.day, 0)
            if not day_solved.get(g.day):
                day_guess_count[g.day] += 1
                if g.bulls == 4:
                    day_solved[g.day] = True
                    days_won.add(g.day)
                    guesses_per_win.append(day_guess_count[g.day])

        avg_guesses = round(sum(guesses_per_win) / len(guesses_per_win), 2) if guesses_per_win else 0
        best_game = min(guesses_per_win) if guesses_per_win else 0

        return {
            "days_played": len(days_played),
            "days_won": len(days_won),
            "win_rate": round(len(days_won) / len(days_played) * 100, 1) if days_played else 0,
            "avg_guesses": avg_guesses,
            "best_game": best_game,
        }