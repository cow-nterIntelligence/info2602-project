from sqlmodel import Session, select, and_
from app.models.friend import Friend
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class FriendRepository:
    def __init__(self, db: Session):
        self.db = db

    def add_friend(self, user_id: int, friend_id: int) -> Friend:
        """Add a friend relationship"""
        if user_id == friend_id:
            raise ValueError("Cannot add yourself as a friend")
        
        # to check if friendship already exists
        existing = self.db.exec(
            select(Friend).where(
                and_(Friend.user_id == user_id, Friend.friend_id == friend_id)
            )
        ).one_or_none()
        
        if existing:
            return existing
        
        try:
            friendship = Friend(user_id=user_id, friend_id=friend_id)
            self.db.add(friendship)
            self.db.commit()
            self.db.refresh(friendship)
            return friendship
        except Exception as e:
            logger.error(f"Error adding friend: {e}")
            self.db.rollback()
            raise

    def remove_friend(self, user_id: int, friend_id: int) -> bool:
        """Remove a friend relationship"""
        try:
            friendship = self.db.exec(
                select(Friend).where(
                    and_(Friend.user_id == user_id, Friend.friend_id == friend_id)
                )
            ).one_or_none()
            
            if friendship:
                self.db.delete(friendship)
                self.db.commit()
                return True
            return False
        except Exception as e:
            logger.error(f"Error removing friend: {e}")
            self.db.rollback()
            raise

    def get_friends(self, user_id: int) -> List[Friend]:
        """Get all friends of a user"""
        return self.db.exec(
            select(Friend).where(Friend.user_id == user_id)
        ).all()

    def get_friend_ids(self, user_id: int) -> List[int]:
        """Get list of friend IDs for a user"""
        friends = self.get_friends(user_id)
        return [f.friend_id for f in friends]

    def is_friend(self, user_id: int, friend_id: int) -> bool:
        """Check if two users are friends"""
        friendship = self.db.exec(
            select(Friend).where(
                and_(Friend.user_id == user_id, Friend.friend_id == friend_id)
            )
        ).one_or_none()
        return friendship is not None

    def get_friend_count(self, user_id: int) -> int:
        """Get the number of friends a user has"""
        return len(self.get_friends(user_id))
