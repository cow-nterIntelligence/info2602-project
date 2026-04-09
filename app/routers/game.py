from fastapi import APIRouter, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlmodel import Session
from datetime import date
from collections import defaultdict

from app.dependencies.session import SessionDep  # Use this instead!
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.repositories.daily_puzzle_repo import get_or_create_today_puzzle
from app.repositories.game_guess_repo import (
    get_user_guesses_today,
    has_user_won_today,
    create_guess,
    get_user_history
)
from app.services.game_service import calculate_bulls_and_cows
from app.main import templates

router = APIRouter(tags=["game"])

@router.get("/app", response_class=HTMLResponse)
def show_game(
    request: Request,
    db_session: SessionDep,  # Just use SessionDep - no Depends() needed!
    user: User = Depends(get_current_user)
):
    """Show today's puzzle - same for ALL users, but guesses are per-user"""
    
    puzzle = get_or_create_today_puzzle(db_session)
    guesses = get_user_guesses_today(db_session, user.id)
    
    if has_user_won_today(db_session, user.id):
        status = "won"
    else:
        status = "playing"
    
    return templates.TemplateResponse("game.html", {
        "request": request,
        "user": user,
        "guesses": guesses,
        "status": status,
        "puzzle": puzzle,
        "reveal_code": status in ("won", "gaveup"),
        "error": None
    })

@router.post("/app")
def handle_guess(
    request: Request,
    db_session: SessionDep,
    user: User = Depends(get_current_user),
    guess: str = Form(None),
    action: str = Form(None)
):
    """Handle guess submission"""
    
    puzzle = get_or_create_today_puzzle(db_session)
    error = None
    
    if action == "giveup":
        return templates.TemplateResponse("game.html", {
            "request": request,
            "user": user,
            "guesses": get_user_guesses_today(db_session, user.id),
            "status": "gaveup",
            "puzzle": puzzle,
            "reveal_code": True,
            "error": None
        })
    
    if guess:
        if len(guess) != 4 or not guess.isdigit() or len(set(guess)) != 4:
            error = "Guess must be 4 unique digits."
        elif has_user_won_today(db_session, user.id):
            error = "You already solved today's puzzle!"
        else:
            bulls, cows = calculate_bulls_and_cows(puzzle, guess)
            is_win = (bulls == 4)
            create_guess(db_session, user.id, guess, bulls, cows, is_win)
            return RedirectResponse(url="/game/app", status_code=303)
    
    guesses = get_user_guesses_today(db_session, user.id)
    status = "won" if has_user_won_today(db_session, user.id) else "playing"
    
    return templates.TemplateResponse("game.html", {
        "request": request,
        "user": user,
        "guesses": guesses,
        "status": status,
        "puzzle": puzzle,
        "reveal_code": status in ("won", "gaveup"),
        "error": error
    })

@router.get("/history", response_class=HTMLResponse)
def game_history(
    request: Request,
    db_session: SessionDep,  # And here
    user: User = Depends(get_current_user)
):
    """View play history"""
    
    guesses = get_user_history(db_session, user.id)
    
    games_by_day = defaultdict(list)
    for g in guesses:
        day_str = g.puzzle_date.strftime("%Y-%m-%d")
        games_by_day[day_str].append(g)
    
    return templates.TemplateResponse("game_history.html", {
        "request": request,
        "user": user,
        "games": dict(games_by_day)
    })