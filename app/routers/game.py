from fastapi import APIRouter, Request, Form
from datetime import date
from app.routers import templates
from app.utilities.game_utils import get_daily_puzzle, bulls_and_cows

router = APIRouter()

@router.get("/app")
async def show_game(request: Request):
    session = request.session
    today = date.today().strftime("%Y-%m-%d")
    # Start/reset session data for today if needed
    if session.get("puzzle_date") != today:
        session["puzzle_date"] = today
        session["guesses"] = []
        session["status"] = "playing"
    user = {"username": "alice"}  # Replace with real user logic

    puzzle = get_daily_puzzle(today)
    context = {
        "request": request,
        "user": user,
        "guesses": session.get("guesses", []),
        "status": session.get("status", "playing"),
        "puzzle": puzzle,
        "reveal_code": session.get("status") in ("won", "gaveup"),
        "error": None
    }
    return templates.TemplateResponse(
        request=request, name="game.html", context=context
    )

@router.post("/app")
async def handle_guess(
    request: Request,
    guess: str = Form(None),
    action: str = Form(None)
):
    session = request.session
    today = date.today().strftime("%Y-%m-%d")
    puzzle = get_daily_puzzle(today)

    # Reset session for a new day if needed
    if session.get("puzzle_date") != today:
        session["puzzle_date"] = today
        session["guesses"] = []
        session["status"] = "playing"

    reveal_code = False
    error = None

    if action == "giveup":
        session["status"] = "gaveup"
        reveal_code = True
    elif guess:
        # Validate input: 4 unique digits, all numbers
        if len(guess) != 4 or not guess.isdigit() or len(set(guess)) != 4:
            error = "Guess must be 4 unique digits."
        else:
            bulls, cows = bulls_and_cows(puzzle, guess)
            session.setdefault("guesses", []).append({
                "guess": guess,
                "bulls": bulls,
                "cows": cows
            })
            if bulls == 4:
                session["status"] = "won"
    user = {"username": "alice"}  # Replace with real user logic
    
    context = {
        "request": request,
        "user": user,
        "guesses": session.get("guesses", []),
        "status": session.get("status", "playing"),
        "puzzle": puzzle,
        "reveal_code": reveal_code or session.get("status") in ("won", "gaveup"),
        "error": error,
    }
    return templates.TemplateResponse(
        request=request, name="game.html", context=context
    )