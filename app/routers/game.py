from fastapi import APIRouter, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import status
from datetime import date

from app.dependencies.auth import AuthDep
from app.dependencies.session import SessionDep
from app.repositories.game import GameRepository
from app.repositories.challenge import ChallengeRepository
from app.utilities.game_utils import get_daily_puzzle, bulls_and_cows
from app.utilities.flash import flash
from app.routers import templates

router = APIRouter()


@router.get("/", response_class=HTMLResponse, name="game_view")
async def game_view(request: Request, user: AuthDep, db: SessionDep):
    today = date.today().strftime("%Y-%m-%d")
    repo = GameRepository(db)
    streak_summary = repo.sync_user_streaks(user.id, today)
    guesses = repo.get_guesses_for_day(user.id, today)
    played_today = repo.has_played_today(user.id, today)
    solved = repo.has_solved_today(user.id, today)
    gave_up = repo.has_given_up_today(user.id, today)
    revealed_code = get_daily_puzzle(today) if solved or gave_up else None
    return templates.TemplateResponse(
        request=request,
        name="game.html",
        context={
            "user": user,
            "guesses": guesses,
            "played_today": played_today,
            "solved": solved,
            "gave_up": gave_up,
            "revealed_code": revealed_code,
            "streak_summary": streak_summary,
        },
    )


@router.post("/guess", name="game_guess")
async def game_guess(request: Request, user: AuthDep, db: SessionDep, guess: str = Form(...)):
    today = date.today().strftime("%Y-%m-%d")
    repo = GameRepository(db)
    challenge_repo = ChallengeRepository(db)

    if repo.has_played_today(user.id, today):
        if repo.has_solved_today(user.id, today):
            flash(request, "You already played today's puzzle and guessed correctly. Come back tomorrow.", "info")
        elif repo.has_given_up_today(user.id, today):
            flash(request, "You already played today's puzzle and gave up. Come back tomorrow.", "info")
        else:
            flash(request, "You already played today's puzzle. Come back tomorrow.", "info")
        return RedirectResponse(url=request.url_for("game_view"), status_code=status.HTTP_302_FOUND)

    if len(guess) != 4 or not guess.isdigit() or len(set(guess)) != 4:
        raise HTTPException(status_code=400, detail="Guess must be exactly 4 unique digits.")

    puzzle = get_daily_puzzle(today)
    bulls, cows = bulls_and_cows(puzzle, guess)
    repo.save_guess(user.id, today, guess, bulls, cows)
    repo.sync_user_streaks(user.id, today)

    # Update challenge results if the user solved the puzzle
    if bulls == 4:
        challenges = challenge_repo.get_challenges_for_day(user.id, today)
        for challenge in challenges:
            if challenge.status in ["pending", "accepted"]:
                guesses = repo.get_guesses_for_day(user.id, today)
                challenge_repo.update_challenge_result(
                    challenge.id,
                    user.id,
                    "solved",
                    len(guesses)
                )

    return RedirectResponse(url=request.url_for("game_view"), status_code=status.HTTP_302_FOUND)


@router.post("/give-up", name="game_give_up")
async def game_give_up(request: Request, user: AuthDep, db: SessionDep):
    today = date.today().strftime("%Y-%m-%d")
    repo = GameRepository(db)
    challenge_repo = ChallengeRepository(db)

    if repo.has_played_today(user.id, today):
        if repo.has_solved_today(user.id, today):
            flash(request, "You already played today's puzzle and guessed correctly. Come back tomorrow.", "info")
        elif repo.has_given_up_today(user.id, today):
            flash(request, "You already played today's puzzle and gave up. Come back tomorrow.", "info")
        else:
            flash(request, "You already played today's puzzle. Come back tomorrow.", "info")
    else:
        repo.save_give_up(user.id, today)
        repo.sync_user_streaks(user.id, today)
        
        # Update challenge results
        challenges = challenge_repo.get_challenges_for_day(user.id, today)
        for challenge in challenges:
            if challenge.status in ["pending", "accepted"]:
                guesses = repo.get_guesses_for_day(user.id, today)
                challenge_repo.update_challenge_result(
                    challenge.id,
                    user.id,
                    "gave_up",
                    len(guesses)
                )

    return RedirectResponse(url=request.url_for("game_view"), status_code=status.HTTP_302_FOUND)


@router.get("/history", response_class=HTMLResponse, name="game_history")
async def game_history(request: Request, user: AuthDep, db: SessionDep):
    repo = GameRepository(db)
    games = repo.get_all_guesses_by_day(user.id)
    stats = repo.get_player_stats(user.id)
    streak_summary = repo.get_streak_summary(user.id)
    return templates.TemplateResponse(
        request=request,
        name="game_history.html",
        context={"user": user, "games": games, "stats": stats, "streak_summary": streak_summary},
    )


@router.get("/leaderboard", response_class=HTMLResponse, name="game_leaderboard")
async def game_leaderboard(request: Request, user: AuthDep, db: SessionDep, day: str = None):
    today = date.today().strftime("%Y-%m-%d")
    selected_day = day if day else today
    repo = GameRepository(db)
    streak_summary = repo.sync_user_streaks(user.id, today)
    leaderboard = repo.get_leaderboard(day=selected_day)
    return templates.TemplateResponse(
        request=request,
        name="game_leaderboard.html",
        context={
            "user": user,
            "leaderboard": leaderboard,
            "selected_day": selected_day,
            "today": today,
            "streak_summary": streak_summary,
        },
    )
