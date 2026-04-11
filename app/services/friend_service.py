from app.repositories.friend import FriendRepository
from app.models.user import User
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class FriendService:
    def __init__(self, friend_repo: FriendRepository):
        self.friend_repo = friend_repo

    def add_friend(self, user_id: int, friend_id: int):
        """Add a friend"""
        return self.friend_repo.add_friend(user_id, friend_id)

    def remove_friend(self, user_id: int, friend_id: int):
        """Remove a friend"""
        return self.friend_repo.remove_friend(user_id, friend_id)

    def get_friends(self, user_id: int):
        """Get all friends"""
        return self.friend_repo.get_friends(user_id)

    def is_friend(self, user_id: int, friend_id: int) -> bool:
        """Check if two users are friends"""
        return self.friend_repo.is_friend(user_id, friend_id)

    def get_friend_count(self, user_id: int) -> int:
        """Get friend count"""
        return self.friend_repo.get_friend_count(user_id)
