from fastapi import APIRouter, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import status
from datetime import date

from app.dependencies.auth import AuthDep
from app.dependencies.session import SessionDep
from app.repositories.challenge import ChallengeRepository
from app.repositories.game import GameRepository
from app.repositories.user import UserRepository
from app.services.challenge_service import ChallengeService
from app.utilities.flash import flash
from app.routers import templates

router = APIRouter()


@router.get("/challenges", response_class=HTMLResponse, name="challenges_view")
async def challenges_view(request: Request, user: AuthDep, db: SessionDep):
    """View all challenges for the current user"""
    challenge_repo = ChallengeRepository(db)
    user_repo = UserRepository(db)
    today = date.today().strftime("%Y-%m-%d")
    
    # Get active and completed challenges
    active_challenges = challenge_repo.get_active_challenges_for_user(user.id)
    pending_challenges = challenge_repo.get_pending_challenges_for_user(user.id)
    completed_challenges = challenge_repo.get_completed_challenges_for_user(user.id)
    
    # Enrich challenges with user information
    def enrich_challenge(challenge):
        if challenge.challenger_id == user.id:
            opponent = user_repo.get_by_id(challenge.opponent_id)
        else:
            opponent = user_repo.get_by_id(challenge.challenger_id)
        return {
            "challenge": challenge,
            "opponent": opponent,
            "is_challenger": challenge.challenger_id == user.id
        }
    
    pending = [enrich_challenge(c) for c in pending_challenges]
    active = [enrich_challenge(c) for c in active_challenges if c.id not in [p["challenge"].id for p in pending]]
    completed = [enrich_challenge(c) for c in completed_challenges]
    
    return templates.TemplateResponse(
        request=request,
        name="challenges.html",
        context={
            "user": user,
            "pending_challenges": pending,
            "active_challenges": active,
            "completed_challenges": completed,
            "today": today,
        },
    )


@router.get("/challenge/{challenge_id}", response_class=HTMLResponse, name="challenge_detail_view")
async def challenge_detail_view(request: Request, user: AuthDep, db: SessionDep, challenge_id: int):
    """View details of a specific challenge"""
    challenge_repo = ChallengeRepository(db)
    game_repo = GameRepository(db)
    user_repo = UserRepository(db)
    
    challenge = challenge_repo.get_challenge_by_id(challenge_id)
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    # Check if user is part of this challenge
    if user.id not in [challenge.challenger_id, challenge.opponent_id]:
        raise HTTPException(status_code=403, detail="Not authorized to view this challenge")
    
    challenger = user_repo.get_by_id(challenge.challenger_id)
    opponent = user_repo.get_by_id(challenge.opponent_id)
    
    # game results
    challenger_guesses = game_repo.get_guesses_for_day(challenge.challenger_id, challenge.day)
    opponent_guesses = game_repo.get_guesses_for_day(challenge.opponent_id, challenge.day)
    
    challenger_solved = game_repo.has_solved_today(challenge.challenger_id, challenge.day)
    opponent_solved = game_repo.has_solved_today(challenge.opponent_id, challenge.day)
    
    challenger_gave_up = game_repo.has_given_up_today(challenge.challenger_id, challenge.day)
    opponent_gave_up = game_repo.has_given_up_today(challenge.opponent_id, challenge.day)
    
    # Determine winner (if challenge is completed)
    winner = None
    if challenge.status == "completed":
        if challenger_solved and not opponent_solved:
            winner = "challenger"
        elif opponent_solved and not challenger_solved:
            winner = "opponent"
        elif challenger_solved and opponent_solved:
            # Both solved, compare guesses
            if challenge.challenger_guesses < challenge.opponent_guesses:
                winner = "challenger"
            elif challenge.opponent_guesses < challenge.challenger_guesses:
                winner = "opponent"
            else:
                winner = "tie"
        else:
            winner = "tie"
    
    # Get head to head record
    record = challenge_repo.get_head_to_head_record(challenge.challenger_id, challenge.opponent_id)
    
    return templates.TemplateResponse(
        request=request,
        name="challenge_detail.html",
        context={
            "user": user,
            "challenge": challenge,
            "challenger": challenger,
            "opponent": opponent,
            "challenger_guesses": challenger_guesses,
            "opponent_guesses": opponent_guesses,
            "challenger_solved": challenger_solved,
            "opponent_solved": opponent_solved,
            "challenger_gave_up": challenger_gave_up,
            "opponent_gave_up": opponent_gave_up,
            "winner": winner,
            "record": record,
            "is_challenger": challenge.challenger_id == user.id,
        },
    )


@router.post("/challenge/create", name="create_challenge")
async def create_challenge(request: Request, user: AuthDep, db: SessionDep, opponent_id: int = Form(...)):
    """Create a new challenge"""
    challenge_repo = ChallengeRepository(db)
    user_repo = UserRepository(db)
    today = date.today().strftime("%Y-%m-%d")
    
    # Verify opponent exists
    opponent = user_repo.get_by_id(opponent_id)
    if not opponent:
        flash(request, "User not found", "error")
        return RedirectResponse(url=request.url_for("friends_view"), status_code=status.HTTP_302_FOUND)
    
    # to see if they already have an active challenge today
    if challenge_repo.has_active_challenge_on_day(user.id, opponent_id, today):
        flash(request, "You already have an active challenge with this user today", "info")
        return RedirectResponse(url=request.url_for("challenges_view"), status_code=status.HTTP_302_FOUND)
    
    try:
        challenge = challenge_repo.create_challenge(user.id, opponent_id, today)
        flash(request, f"Challenge sent to {opponent.username}!", "success")
    except Exception as e:
        flash(request, f"Error creating challenge: {str(e)}", "error")
    
    return RedirectResponse(url=request.url_for("challenges_view"), status_code=status.HTTP_302_FOUND)


@router.post("/challenge/{challenge_id}/accept", name="accept_challenge")
async def accept_challenge(request: Request, user: AuthDep, db: SessionDep, challenge_id: int):
    """Accept a pending challenge"""
    challenge_repo = ChallengeRepository(db)
    
    challenge = challenge_repo.get_challenge_by_id(challenge_id)
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    if challenge.opponent_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to accept this challenge")
    
    if challenge.status != "pending":
        flash(request, "Challenge is no longer pending", "info")
        return RedirectResponse(url=request.url_for("challenges_view"), status_code=status.HTTP_302_FOUND)
    
    try:
        challenge_repo.update_challenge_status(challenge_id, "accepted")
        flash(request, "Challenge accepted! Now let's see who solves it first.", "success")
    except Exception as e:
        flash(request, f"Error accepting challenge: {str(e)}", "error")
    
    return RedirectResponse(url=request.url_for("challenge_detail_view", challenge_id=challenge_id), status_code=status.HTTP_302_FOUND)


@router.post("/challenge/{challenge_id}/decline", name="decline_challenge")
async def decline_challenge(request: Request, user: AuthDep, db: SessionDep, challenge_id: int):
    """Decline a pending challenge"""
    challenge_repo = ChallengeRepository(db)
    
    challenge = challenge_repo.get_challenge_by_id(challenge_id)
    if not challenge:
        raise HTTPException(status_code=404, detail="Challenge not found")
    
    if challenge.opponent_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to decline this challenge")
    
    try:
        # dlt the challenge (or set status to declined)
        db.delete(challenge)
        db.commit()
        flash(request, "Challenge declined", "success")
    except Exception as e:
        flash(request, f"Error declining challenge: {str(e)}", "error")
    
    return RedirectResponse(url=request.url_for("challenges_view"), status_code=status.HTTP_302_FOUND)
