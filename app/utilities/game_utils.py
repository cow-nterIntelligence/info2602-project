import hashlib
import random
from datetime import date

def get_daily_puzzle(day: str = None):
    if day is None:
        day = date.today().strftime("%Y-%m-%d")
    seed = int(hashlib.sha256(day.encode()).hexdigest(), 16)
    digits = list("0123456789")
    random.seed(seed)
    puzzle = ""
    while len(puzzle) < 4:
        d = random.choice(digits)
        if d not in puzzle:
            puzzle += d
    return puzzle

def bulls_and_cows(secret, guess):
    bulls = sum(a == b for a, b in zip(secret, guess))
    cows = sum(min(secret.count(x), guess.count(x)) for x in set(guess)) - bulls
    return bulls, cows