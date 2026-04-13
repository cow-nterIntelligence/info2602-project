from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import status

from app.dependencies.auth import AuthDep
from app.dependencies.session import SessionDep
from app.repositories.friend import FriendRepository
from app.repositories.game import GameRepository
from app.repositories.user import UserRepository
from app.utilities.security import encrypt_password, verify_password
from app.utilities.flash import flash
from fastapi.templating import Jinja2Templates
from jinja2 import Environment, FileSystemLoader
from app.utilities.flash import get_flashed_messages
from datetime import date

template_env = Environment(loader=FileSystemLoader("app/templates"))
template_env.globals['get_flashed_messages'] = get_flashed_messages
templates = Jinja2Templates(env=template_env)


router = APIRouter()


@router.get("/profile", response_class=HTMLResponse, name="profile_view")
async def profile_view(request: Request, user: AuthDep, db: SessionDep):
    today = date.today().strftime("%Y-%m-%d")

    # player stats 
    game_repo = GameRepository(db)
    stats = game_repo.get_player_stats(user.id)
    streak_summary = game_repo.get_streak_summary(user.id)

    # friends list
    friend_repo = FriendRepository(db)
    user_repo = UserRepository(db)
    friend_ids = friend_repo.get_friend_ids(user.id)

    # friend activity feed
    friend_activity = []
    for friend_id in friend_ids:
        friend = user_repo.get_by_id(friend_id)
        if not friend:
            continue
        friend_stats = game_repo.get_player_stats(friend_id)
        friend_guesses_today = game_repo.get_guesses_for_day(friend_id, today)
        solved_today = any(g.bulls == 4 for g in friend_guesses_today)
        gave_up_today = any(g.guess == "GAVE_UP" for g in friend_guesses_today)
        played_today = len(friend_guesses_today) > 0

        friend_activity.append({
            "username": friend.username,
            "current_streak": friend_stats["current_streak"],
            "longest_streak": friend_stats["longest_streak"],
            "badge": friend_stats["badge"],
            "solved_today": solved_today,
            "gave_up_today": gave_up_today,
            "played_today": played_today,
            "guess_count_today": len([
                g for g in friend_guesses_today
                if g.guess != "GAVE_UP"
            ]),
        })

    return templates.TemplateResponse(
        request=request,
        name="profile.html",
        context={
            "user": user,
            "stats": stats,
            "streak_summary": streak_summary,
            "friend_activity": friend_activity,
            "friend_count": len(friend_ids),
        },
    )


@router.post("/profile/change-password", name="change_password")
async def change_password(
    request: Request,
    user: AuthDep,
    db: SessionDep,
    current_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...),
):
    # check current password is correct
    if not verify_password(current_password, user.password):
        flash(request, "Current password is incorrect.", "danger")
        return RedirectResponse(
            url=request.url_for("profile_view"),
            status_code=status.HTTP_302_FOUND
        )

    # check new passwords match
    if new_password != confirm_password:
        flash(request, "New passwords do not match.", "danger")
        return RedirectResponse(
            url=request.url_for("profile_view"),
            status_code=status.HTTP_302_FOUND
        )

    # check new password isn't too short
    if len(new_password) < 8:
        flash(request, "New password must be at least 8 characters.", "danger")
        return RedirectResponse(
            url=request.url_for("profile_view"),
            status_code=status.HTTP_302_FOUND
        )

    # save the new hashed password
    user_repo = UserRepository(db)
    db_user = user_repo.get_by_id(user.id)
    db_user.password = encrypt_password(new_password)
    db.add(db_user)
    db.commit()

    flash(request, "Password updated successfully!", "success")
    return RedirectResponse(
        url=request.url_for("profile_view"),
        status_code=status.HTTP_302_FOUND
    )
