from sqlmodel import Session, select, and_, or_
from app.models.friend import Friend
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class FriendRepository:
    def __init__(self, db: Session):
        self.db = db

    # ------------------------------------------------------------------
    # Friend requests
    # ------------------------------------------------------------------

    def send_friend_request(self, user_id: int, friend_id: int) -> Friend:
        """Send a friend request (creates a pending record)"""
        if user_id == friend_id:
            raise ValueError("Cannot add yourself as a friend")

        # Check if any relationship already exists in either direction
        existing = self.db.exec(
            select(Friend).where(
                or_(
                    and_(Friend.user_id == user_id, Friend.friend_id == friend_id),
                    and_(Friend.user_id == friend_id, Friend.friend_id == user_id),
                )
            )
        ).one_or_none()

        if existing:
            if existing.status == "accepted":
                raise ValueError("You are already friends with this user")
            elif existing.status == "pending":
                raise ValueError("A friend request already exists between you and this user")

        try:
            friendship = Friend(user_id=user_id, friend_id=friend_id, status="pending")
            self.db.add(friendship)
            self.db.commit()
            self.db.refresh(friendship)
            return friendship
        except Exception as e:
            logger.error(f"Error sending friend request: {e}")
            self.db.rollback()
            raise

    def accept_friend_request(self, request_id: int, user_id: int) -> Friend:
        """Accept a pending friend request (the recipient accepts)"""
        friendship = self.db.get(Friend, request_id)
        if not friendship:
            raise ValueError("Friend request not found")
        if friendship.friend_id != user_id:
            raise ValueError("Not authorized to accept this request")
        if friendship.status != "pending":
            raise ValueError("Request is not pending")

        try:
            friendship.status = "accepted"
            self.db.add(friendship)
            self.db.commit()
            self.db.refresh(friendship)
            return friendship
        except Exception as e:
            logger.error(f"Error accepting friend request: {e}")
            self.db.rollback()
            raise

    def decline_friend_request(self, request_id: int, user_id: int) -> bool:
        """Decline or cancel a pending friend request"""
        friendship = self.db.get(Friend, request_id)
        if not friendship:
            raise ValueError("Friend request not found")
        # Allow both requester (cancel) and recipient (decline) to delete
        if friendship.user_id != user_id and friendship.friend_id != user_id:
            raise ValueError("Not authorized to decline this request")

        try:
            self.db.delete(friendship)
            self.db.commit()
            return True
        except Exception as e:
            logger.error(f"Error declining friend request: {e}")
            self.db.rollback()
            raise

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_friends(self, user_id: int) -> List[Friend]:
        """Get all ACCEPTED friendships for a user (in either direction)"""
        return self.db.exec(
            select(Friend).where(
                and_(
                    or_(Friend.user_id == user_id, Friend.friend_id == user_id),
                    Friend.status == "accepted",
                )
            )
        ).all()

    def get_friend_ids(self, user_id: int) -> List[int]:
        """Get list of friend IDs for a user (accepted only)"""
        friends = self.get_friends(user_id)
        return [
            f.friend_id if f.user_id == user_id else f.user_id
            for f in friends
        ]

    def get_pending_requests_received(self, user_id: int) -> List[Friend]:
        """Get pending friend requests received by this user"""
        return self.db.exec(
            select(Friend).where(
                and_(Friend.friend_id == user_id, Friend.status == "pending")
            )
        ).all()

    def get_pending_requests_sent(self, user_id: int) -> List[Friend]:
        """Get pending friend requests sent by this user"""
        return self.db.exec(
            select(Friend).where(
                and_(Friend.user_id == user_id, Friend.status == "pending")
            )
        ).all()

    def remove_friend(self, user_id: int, friend_id: int) -> bool:
        """Remove an accepted friendship (in either direction)"""
        try:
            friendship = self.db.exec(
                select(Friend).where(
                    and_(
                        or_(
                            and_(Friend.user_id == user_id, Friend.friend_id == friend_id),
                            and_(Friend.user_id == friend_id, Friend.friend_id == user_id),
                        ),
                        Friend.status == "accepted",
                    )
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

    def is_friend(self, user_id: int, friend_id: int) -> bool:
        """Check if two users are accepted friends (either direction)"""
        friendship = self.db.exec(
            select(Friend).where(
                and_(
                    or_(
                        and_(Friend.user_id == user_id, Friend.friend_id == friend_id),
                        and_(Friend.user_id == friend_id, Friend.friend_id == user_id),
                    ),
                    Friend.status == "accepted",
                )
            )
        ).one_or_none()
        return friendship is not None

    def has_pending_request(self, user_id: int, friend_id: int) -> Optional[str]:
        """Return direction of pending request: 'sent', 'received', or None"""
        friendship = self.db.exec(
            select(Friend).where(
                and_(
                    or_(
                        and_(Friend.user_id == user_id, Friend.friend_id == friend_id),
                        and_(Friend.user_id == friend_id, Friend.friend_id == user_id),
                    ),
                    Friend.status == "pending",
                )
            )
        ).one_or_none()
        if not friendship:
            return None
        return "sent" if friendship.user_id == user_id else "received"

    def get_friend_count(self, user_id: int) -> int:
        """Get the number of accepted friends a user has"""
        return len(self.get_friends(user_id))

    # Kept for backward-compat; now routes through send_friend_request
    def add_friend(self, user_id: int, friend_id: int) -> Friend:
        return self.send_friend_request(user_id, friend_id)
