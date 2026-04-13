from app.repositories.friend import FriendRepository
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class FriendService:
    def __init__(self, friend_repo: FriendRepository):
        self.friend_repo = friend_repo

    def send_friend_request(self, user_id: int, friend_id: int):
        """Send a friend request (creates pending record)"""
        return self.friend_repo.send_friend_request(user_id, friend_id)

    def accept_friend_request(self, request_id: int, user_id: int):
        """Accept a pending friend request"""
        return self.friend_repo.accept_friend_request(request_id, user_id)

    def decline_friend_request(self, request_id: int, user_id: int):
        """Decline or cancel a friend request"""
        return self.friend_repo.decline_friend_request(request_id, user_id)

    def remove_friend(self, user_id: int, friend_id: int):
        """Remove an accepted friendship"""
        return self.friend_repo.remove_friend(user_id, friend_id)

    def get_friends(self, user_id: int):
        """Get all accepted friends"""
        return self.friend_repo.get_friends(user_id)

    def get_pending_requests_received(self, user_id: int):
        """Get pending requests received by user"""
        return self.friend_repo.get_pending_requests_received(user_id)

    def get_pending_requests_sent(self, user_id: int):
        """Get pending requests sent by user"""
        return self.friend_repo.get_pending_requests_sent(user_id)

    def is_friend(self, user_id: int, friend_id: int) -> bool:
        """Check if two users are accepted friends"""
        return self.friend_repo.is_friend(user_id, friend_id)

    def get_friend_count(self, user_id: int) -> int:
        """Get friend count"""
        return self.friend_repo.get_friend_count(user_id)

    # Backward-compat alias
    def add_friend(self, user_id: int, friend_id: int):
        return self.send_friend_request(user_id, friend_id)
