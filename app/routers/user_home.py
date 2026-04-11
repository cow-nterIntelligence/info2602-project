from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import status
from app.dependencies.session import SessionDep
from app.dependencies.auth import AuthDep, IsUserLoggedIn, get_current_user, is_admin
from . import router, templates
from app.repositories.guess import GuessRepository
from datetime import date
from app.utilities.game_utils import get_daily_puzzle


@router.get("/app", response_class=HTMLResponse)
async def user_home_view(
    request: Request,
    user: AuthDep,
    db: SessionDep
):
    today = date.today().strftime("%Y-%m-%d")
    
    # Check if user has completed today's game
    guess_repo = GuessRepository(db)
    completed = guess_repo.has_completed_game(user.id, today)
    
    if completed:
        # Show summary on home page
        db_guesses = guess_repo.get_guesses_by_user_and_date(user.id, today)
        guesses = [
            {"guess": g.guess, "bulls": g.bulls, "cows": g.cows}
            for g in db_guesses if g.action == "guess"
        ]
        status = guess_repo.get_game_status(user.id, today)
        puzzle = get_daily_puzzle(today)
        
        return templates.TemplateResponse(
            request=request, 
            name="game.html",
            context={
                "user": user,
                "completed": True,
                "status": status,
                "guesses": guesses,
                "puzzle": puzzle,
                "reveal_code": True,
                "error": None
            }
        )
    else:
        # Redirect to game page
        return RedirectResponse(url="/game/app", status_code=302)