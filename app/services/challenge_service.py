from app.repositories.challenge import ChallengeRepository
from app.repositories.game import GameRepository
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)


class ChallengeService:
    def __init__(self, challenge_repo: ChallengeRepository, game_repo: GameRepository):
        self.challenge_repo = challenge_repo
        self.game_repo = game_repo

    def create_challenge(self, challenger_id: int, opponent_id: int, day: str):
        """Create a new challenge"""
        #if they already have an active challenge on this day
        if self.challenge_repo.has_active_challenge_on_day(challenger_id, opponent_id, day):
            raise ValueError("An active challenge already exists between these users for this day")
        return self.challenge_repo.create_challenge(challenger_id, opponent_id, day)

    def get_challenge(self, challenge_id: int):
        """Get a challenge by ID"""
        return self.challenge_repo.get_challenge_by_id(challenge_id)

    def get_pending_challenges(self, user_id: int):
        """Get pending challenges for a user"""
        return self.challenge_repo.get_pending_challenges_for_user(user_id)

    def get_active_challenges(self, user_id: int):
        """Get active challenges for a user"""
        return self.challenge_repo.get_active_challenges_for_user(user_id)

    def get_completed_challenges(self, user_id: int):
        """Get completed challenges for a user"""
        return self.challenge_repo.get_completed_challenges_for_user(user_id)

    def get_challenges_for_day(self, user_id: int, day: str):
        """Get challenges for a user on a specific day"""
        return self.challenge_repo.get_challenges_for_day(user_id, day)

    def update_user_challenge_result(self, challenge_id: int, user_id: int, day: str):
        """Update challenge result based on game outcome for the user"""
        challenge = self.challenge_repo.get_challenge_by_id(challenge_id)
        if not challenge:
            raise ValueError(f"Challenge {challenge_id} not found")
      
        guesses = self.game_repo.get_guesses_for_day(user_id, day)
        
        result = None
        guess_count = None
        
        if self.game_repo.has_solved_today(user_id, day):
            result = "solved"
            guess_count = len(guesses)
        elif self.game_repo.has_given_up_today(user_id, day):
            result = "gave_up"
            guess_count = len(guesses)
        
        if result:
            return self.challenge_repo.update_challenge_result(
                challenge_id, user_id, result, guess_count
            )
        return challenge

    def get_head_to_head_record(self, user_id1: int, user_id2: int):
        """Get head-to-head record between two users"""
        return self.challenge_repo.get_head_to_head_record(user_id1, user_id2)
