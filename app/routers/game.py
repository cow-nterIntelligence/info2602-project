from fastapi import APIRouter, HTTPException
from app.utilities.game_utils import get_daily_puzzle, bulls_and_cows  # Adjust as needed

from datetime import date

router = APIRouter()

@router.get("/puzzle")
def show_info():
    # Optionally provide info about today's puzzle (do not reveal the answer!)
    return {"message": "There is one puzzle per day for everyone. Use /guess/{guess} to play."}

@router.get("/guess/{guess}")
def make_guess(guess: str):
    if len(guess) != 4 or not guess.isdigit() or len(set(guess)) != 4:
        raise HTTPException(status_code=400, detail="Guess must be 4 unique digits.")
    today = date.today().strftime("%Y-%m-%d")
    puzzle = get_daily_puzzle(today)
    bulls, cows = bulls_and_cows(puzzle, guess)
    solved = bulls == 4
    return {"bulls": bulls, "cows": cows, "solved": solved}
     
