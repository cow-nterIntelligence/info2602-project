from fastapi import APIRouter, Request, Form
from datetime import date
from app.routers import templates
from app.utilities.game_utils import get_daily_puzzle, bulls_and_cows
from app.models.game_guess import Guess
from app.repositories.guess import GuessRepository
from app.dependencies.auth import AuthDep
from app.dependencies.session import SessionDep 

router = APIRouter()

@router.get("/app")
async def show_game(request: Request, user: AuthDep, db: SessionDep):
    today = date.today().strftime("%Y-%m-%d")

    # Get guesses from database
    guess_repo = GuessRepository(db)
    db_guesses = guess_repo.get_guesses_by_user_and_date(user.id, today)

    # Convert to the format expected by template
    guesses = [
        {"guess": g.guess, "bulls": g.bulls, "cows": g.cows}
        for g in db_guesses
    ]

    # Determine game status based on guesses
    status = guess_repo.get_game_status(user.id, today)
    completed = guess_repo.has_completed_game(user.id, today)

    puzzle = get_daily_puzzle(today)
    context = {
        "request": request,
        "user": user,
        "guesses": guesses,
        "status": status,
        "puzzle": puzzle,
        "reveal_code": status in ("won", "gaveup"),
        "completed": completed,
        "error": None
    }
    return templates.TemplateResponse(
        request=request, name="game.html", context=context
    )

@router.post("/app")
async def handle_guess(
    request: Request,
    user: AuthDep,
    db: SessionDep,
    guess: str = Form(None),
    action: str = Form(None)
):
    today = date.today().strftime("%Y-%m-%d")
    puzzle = get_daily_puzzle(today)

    guess_repo = GuessRepository(db)
    db_guesses = guess_repo.get_guesses_by_user_and_date(user.id, today)

    # Convert to list format for processing
    guesses = [
        {"guess": g.guess, "bulls": g.bulls, "cows": g.cows}
        for g in db_guesses
    ]

    # Determine current status
    status = guess_repo.get_game_status(user.id, today)
    completed = guess_repo.has_completed_game(user.id, today)

    reveal_code = False
    error = None

    if completed:
        error = "You have already completed today's game."
    elif action == "giveup":
        # Save giveup action
        giveup_guess = Guess(
            user_id=user.id,
            puzzle_date=today,
            guess="",  # Empty guess for giveup
            bulls=0,
            cows=0,
            action="giveup"
        )
        guess_repo.create(giveup_guess)
        status = "gaveup"
        reveal_code = True
        completed = True
    elif guess and status == "playing":
        # Validate input: 4 unique digits, all numbers
        if len(guess) != 4 or not guess.isdigit() or len(set(guess)) != 4:
            error = "Guess must be 4 unique digits."
        else:
            # Check if guess already exists
            if any(g["guess"] == guess for g in guesses):
                error = "You already guessed that number."
            else:
                bulls, cows = bulls_and_cows(puzzle, guess)

                # Save to database
                new_guess = Guess(
                    user_id=user.id,
                    puzzle_date=today,
                    guess=guess,
                    bulls=bulls,
                    cows=cows,
                    action="guess"
                )
                guess_repo.create(new_guess)

                guesses.append({
                    "guess": guess,
                    "bulls": bulls,
                    "cows": cows
                })

                if bulls == 4:
                    status = "won"
                    reveal_code = True
                    completed = True

    context = {
        "request": request,
        "user": user,
        "guesses": guesses,
        "status": status,
        "puzzle": puzzle,
        "reveal_code": reveal_code or status in ("won", "gaveup"),
        "completed": completed,
        "error": error,
    }
    return templates.TemplateResponse(
        request=request, name="game.html", context=context)