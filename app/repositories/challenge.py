from sqlmodel import Session, select, and_
from sqlalchemy import or_
from app.models.challenge import Challenge
from app.models.user import User
from datetime import datetime
from typing import Optional, List, Tuple
import logging

logger = logging.getLogger(__name__)


class ChallengeRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_challenge(self, challenger_id: int, opponent_id: int, day: str) -> Challenge:
        """Create a new challenge"""
        if challenger_id == opponent_id:
            raise ValueError("Cannot challenge yourself")
        
        try:
            challenge = Challenge(
                challenger_id=challenger_id,
                opponent_id=opponent_id,
                day=day,
                status="pending"
            )
            self.db.add(challenge)
            self.db.commit()
            self.db.refresh(challenge)
            return challenge
        except Exception as e:
            logger.error(f"Error creating challenge: {e}")
            self.db.rollback()
            raise

    def get_challenge_by_id(self, challenge_id: int) -> Optional[Challenge]:
        """Get a challenge by ID"""
        return self.db.get(Challenge, challenge_id)

    def get_pending_challenges_for_user(self, user_id: int) -> List[Challenge]:
        """Get all pending challenges where user is the opponent"""
        return self.db.exec(
            select(Challenge).where(
                and_(Challenge.opponent_id == user_id, Challenge.status == "pending")
            )
        ).all()

    def get_active_challenges_for_user(self, user_id: int) -> List[Challenge]:
        """Get all active challenges for a user (challenger or opponent)"""
        return self.db.exec(
            select(Challenge).where(
                and_(
                    or_(Challenge.challenger_id == user_id, Challenge.opponent_id == user_id),
                    Challenge.status.in_(["pending", "accepted"])
                )
            )
        ).all()

    def get_completed_challenges_for_user(self, user_id: int) -> List[Challenge]:
        """Get all completed challenges for a user"""
        return self.db.exec(
            select(Challenge).where(
                and_(
                    or_(Challenge.challenger_id == user_id, Challenge.opponent_id == user_id),
                    Challenge.status == "completed"
                )
            ).order_by(Challenge.completed_at.desc())
        ).all()

    def get_challenges_for_day(self, user_id: int, day: str) -> List[Challenge]:
        """Get all challenges for a user on a specific day"""
        return self.db.exec(
            select(Challenge).where(
                and_(
                    or_(Challenge.challenger_id == user_id, Challenge.opponent_id == user_id),
                    Challenge.day == day
                )
            )
        ).all()

    def update_challenge_status(self, challenge_id: int, status: str):
        """Update challenge status"""
        challenge = self.get_challenge_by_id(challenge_id)
        if not challenge:
            raise ValueError(f"Challenge {challenge_id} not found")
        
        try:
            challenge.status = status
            if status == "completed":
                challenge.completed_at = datetime.utcnow()
            self.db.add(challenge)
            self.db.commit()
            self.db.refresh(challenge)
            return challenge
        except Exception as e:
            logger.error(f"Error updating challenge status: {e}")
            self.db.rollback()
            raise

    def update_challenge_result(
        self,
        challenge_id: int,
        user_id: int,
        result: str,  # 'solved' or 'gave_up'
        guesses: Optional[int] = None
    ):
        """Update challenge result for a user"""
        challenge = self.get_challenge_by_id(challenge_id)
        if not challenge:
            raise ValueError(f"Challenge {challenge_id} not found")
        
        if user_id == challenge.challenger_id:
            challenge.challenger_result = result
            challenge.challenger_guesses = guesses
        elif user_id == challenge.opponent_id:
            challenge.opponent_result = result
            challenge.opponent_guesses = guesses
        else:
            raise ValueError("User is not part of this challenge")
        
        try:
            # Check if both players have completed
            if challenge.challenger_result and challenge.opponent_result:
                challenge.status = "completed"
                challenge.completed_at = datetime.utcnow()
            
            self.db.add(challenge)
            self.db.commit()
            self.db.refresh(challenge)
            return challenge
        except Exception as e:
            logger.error(f"Error updating challenge result: {e}")
            self.db.rollback()
            raise

    def has_active_challenge_on_day(self, user_id1: int, user_id2: int, day: str) -> bool:
        """Check if two users have an active challenge on a specific day"""
        challenge = self.db.exec(
            select(Challenge).where(
                and_(
                    or_(
                        and_(Challenge.challenger_id == user_id1, Challenge.opponent_id == user_id2),
                        and_(Challenge.challenger_id == user_id2, Challenge.opponent_id == user_id1)
                    ),
                    Challenge.day == day,
                    Challenge.status.in_(["pending", "accepted"])
                )
            )
        ).one_or_none()
        return challenge is not None

    def get_head_to_head_record(self, user_id1: int, user_id2: int) -> dict:
        """Get head-to-head record between two users"""
        challenges = self.db.exec(
            select(Challenge).where(
                and_(
                    or_(
                        and_(Challenge.challenger_id == user_id1, Challenge.opponent_id == user_id2),
                        and_(Challenge.challenger_id == user_id2, Challenge.opponent_id == user_id1)
                    ),
                    Challenge.status == "completed"
                )
            )
        ).all()
        
        user1_wins = 0
        user2_wins = 0
        draws = 0
        
        for challenge in challenges:
            if challenge.challenger_result == "solved" and challenge.opponent_result != "solved":
                if challenge.challenger_id == user_id1:
                    user1_wins += 1
                else:
                    user2_wins += 1
            elif challenge.opponent_result == "solved" and challenge.challenger_result != "solved":
                if challenge.opponent_id == user_id1:
                    user1_wins += 1
                else:
                    user2_wins += 1
            elif challenge.challenger_result == "solved" and challenge.opponent_result == "solved":
                if challenge.challenger_guesses < challenge.opponent_guesses:
                    if challenge.challenger_id == user_id1:
                        user1_wins += 1
                    else:
                        user2_wins += 1
                elif challenge.opponent_guesses < challenge.challenger_guesses:
                    if challenge.opponent_id == user_id1:
                        user1_wins += 1
                    else:
                        user2_wins += 1
                else:
                    draws += 1
            else:
                draws += 1
        
        return {
            "user1_id": user_id1,
            "user2_id": user_id2,
            "user1_wins": user1_wins,
            "user2_wins": user2_wins,
            "draws": draws,
            "total": len(challenges)
        }
