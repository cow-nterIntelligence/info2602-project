from fastapi import APIRouter
import random

router = APIRouter()

secret_number =""

@router.get("/start")
def start_game():
    global secret_number
    secret_number = "".join(random.sample("0123456789", 4))
    return {"message": "Game started! Guess the 4 digit number."}

@router.get("/guess/{guess}")
def make_guess(guess:str):
    if len(guess)!=4 or not guess.isdigit():
        return {"ERROR": "Invalid guess. Please enter a 4 digit number."}

        bulls = sum(a == b for a, b in zip(secret_number,guess))
        cows = sum(min(secret_number.count(x), guess.count(x)) for x in set(guess)) - bulls
        return {"bulls": bulls, "cows": cows}
        
