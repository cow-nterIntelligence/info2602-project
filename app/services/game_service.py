import random
from datetime import date

def generate_secret_number() -> str:
    """Generate 4 unique random digits"""
    digits = random.sample(range(10), 4)
    return ''.join(map(str, digits))

def calculate_bulls_and_cows(secret: str, guess: str) -> tuple[int, int]:
    """Calculate bulls (correct position) and cows (wrong position)"""
    bulls = 0
    cows = 0
    secret_list = list(secret)
    guess_list = list(guess)
    
    # Count bulls first
    for i in range(4):
        if guess_list[i] == secret_list[i]:
            bulls += 1
            secret_list[i] = guess_list[i] = None
    
    # Count cows
    for i in range(4):
        if guess_list[i] is not None and guess_list[i] in secret_list:
            cows += 1
            secret_list[secret_list.index(guess_list[i])] = None
    
    return bulls, cows