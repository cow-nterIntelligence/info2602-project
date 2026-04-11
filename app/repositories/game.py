from sqlmodel import Session, select
from app.models.game_guess import GameGuess
from app.models.user import User
from datetime import date, datetime, timedelta
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class GameRepository:
    GIVE_UP_MARKER = "GAVE_UP"

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

    def has_played_today(self, user_id: int, day: str) -> bool:
        guesses = self.get_guesses_for_day(user_id, day)
        return len(guesses) > 0

    def has_given_up_today(self, user_id: int, day: str) -> bool:
        guesses = self.get_guesses_for_day(user_id, day)
        return any(g.guess == self.GIVE_UP_MARKER for g in guesses)

    def has_completed_today(self, user_id: int, day: str) -> bool:
        return self.has_solved_today(user_id, day) or self.has_given_up_today(user_id, day)

    def save_give_up(self, user_id: int, day: str) -> GameGuess:
        return self.save_guess(
            user_id=user_id,
            day=day,
            guess=self.GIVE_UP_MARKER,
            bulls=-1,
            cows=-1,
        )

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

    def get_streak_badge(self, longest_streak: int) -> Optional[dict]:
        if longest_streak >= 14:
            return {"name": "Crown Of The Herd", "icon": "workspace_premium"}
        if longest_streak >= 7:
            return {"name": "Golden Bull", "icon": "military_tech"}
        if longest_streak >= 3:
            return {"name": "Hot Streak", "icon": "local_fire_department"}
        if longest_streak >= 1:
            return {"name": "First Win", "icon": "verified"}
        return None

    def get_streak_summary(self, user_id: int, today: Optional[str] = None) -> dict:
        if today is None:
            today = date.today().strftime("%Y-%m-%d")

        today_date = datetime.strptime(today, "%Y-%m-%d").date()
        stmt = (
            select(GameGuess)
            .where(GameGuess.user_id == user_id)
            .order_by(GameGuess.day, GameGuess.timestamp)
        )
        guesses = self.db.exec(stmt).all()

        solved_days = sorted({
            datetime.strptime(g.day, "%Y-%m-%d").date()
            for g in guesses
            if g.bulls == 4
        })
        played_today = any(g.day == today for g in guesses)
        solved_today = any(g.day == today and g.bulls == 4 for g in guesses)

        longest_streak = 0
        running_streak = 0
        previous_day = None
        for solved_day in solved_days:
            if previous_day and solved_day == previous_day + timedelta(days=1):
                running_streak += 1
            else:
                running_streak = 1
            longest_streak = max(longest_streak, running_streak)
            previous_day = solved_day

        current_streak = 0
        if solved_days:
            latest_solved = solved_days[-1]
            if played_today and not solved_today:
                current_streak = 0
            elif latest_solved >= today_date - timedelta(days=1):
                current_streak = 1
                cursor = latest_solved
                solved_set = set(solved_days)
                while cursor - timedelta(days=1) in solved_set:
                    current_streak += 1
                    cursor -= timedelta(days=1)

        last_solved_day = solved_days[-1].strftime("%Y-%m-%d") if solved_days else None
        return {
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "last_solved_day": last_solved_day,
            "badge": self.get_streak_badge(longest_streak),
        }

    def sync_user_streaks(self, user_id: int, today: Optional[str] = None) -> dict:
        summary = self.get_streak_summary(user_id=user_id, today=today)
        user = self.db.get(User, user_id)
        if user and (
            user.current_streak != summary["current_streak"]
            or user.longest_streak != summary["longest_streak"]
        ):
            user.current_streak = summary["current_streak"]
            user.longest_streak = summary["longest_streak"]
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
        return summary

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
            day_solved.setdefault(g.day, False)

            if g.guess == self.GIVE_UP_MARKER:
                continue

            day_guess_count.setdefault(g.day, 0)
            if not day_solved.get(g.day):
                day_guess_count[g.day] += 1
                if g.bulls == 4:
                    day_solved[g.day] = True
                    days_won.add(g.day)
                    guesses_per_win.append(day_guess_count[g.day])

        avg_guesses = round(sum(guesses_per_win) / len(guesses_per_win), 2) if guesses_per_win else 0
        best_game = min(guesses_per_win) if guesses_per_win else 0

        streak_summary = self.sync_user_streaks(user_id)

        return {
            "days_played": len(days_played),
            "days_won": len(days_won),
            "win_rate": round(len(days_won) / len(days_played) * 100, 1) if days_played else 0,
            "avg_guesses": avg_guesses,
            "best_game": best_game,
            "current_streak": streak_summary["current_streak"],
            "longest_streak": streak_summary["longest_streak"],
            "last_solved_day": streak_summary["last_solved_day"],
            "badge": streak_summary["badge"],
        }
