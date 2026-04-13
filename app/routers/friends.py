from fastapi import APIRouter, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi import status

from app.dependencies.auth import AuthDep
from app.dependencies.session import SessionDep
from app.repositories.friend import FriendRepository
from app.repositories.user import UserRepository
from app.utilities.flash import flash
from app.routers import templates

router = APIRouter()


@router.get("/friends", response_class=HTMLResponse, name="friends_view")
async def friends_view(request: Request, user: AuthDep, db: SessionDep):
    """View all friends and pending requests"""
    friend_repo = FriendRepository(db)
    user_repo = UserRepository(db)

    # Accepted friends (bidirectional)
    friends_rel = friend_repo.get_friends(user.id)
    friends = []
    for f in friends_rel:
        other_id = f.friend_id if f.user_id == user.id else f.user_id
        other = user_repo.get_by_id(other_id)
        if other:
            friends.append(other)

    # Pending requests this user received (they need to accept/decline)
    received_rels = friend_repo.get_pending_requests_received(user.id)
    pending_received = []
    for f in received_rels:
        requester = user_repo.get_by_id(f.user_id)
        if requester:
            pending_received.append({"request_id": f.id, "user": requester})

    # Pending requests this user sent (waiting for the other person)
    sent_rels = friend_repo.get_pending_requests_sent(user.id)
    pending_sent = []
    for f in sent_rels:
        recipient = user_repo.get_by_id(f.friend_id)
        if recipient:
            pending_sent.append({"request_id": f.id, "user": recipient})

    return templates.TemplateResponse(
        request=request,
        name="friends.html",
        context={
            "user": user,
            "friends": friends,
            "pending_received": pending_received,
            "pending_sent": pending_sent,
        },
    )


@router.get("/search-users", response_class=HTMLResponse, name="search_users_view")
async def search_users_view(request: Request, user: AuthDep, db: SessionDep, q: str = ""):
    """Search for users to add as friends"""
    user_repo = UserRepository(db)
    friend_repo = FriendRepository(db)

    search_results = []
    if q:
        results, _ = user_repo.search_users(q, page=1, limit=10)
        results = [u for u in results if u.id != user.id]
        friend_ids = friend_repo.get_friend_ids(user.id)
        search_results = []
        for u in results:
            pending_direction = friend_repo.has_pending_request(user.id, u.id)
            search_results.append(
                {
                    "id": u.id,
                    "username": u.username,
                    "email": u.email,
                    "is_friend": u.id in friend_ids,
                    "request_sent": pending_direction == "sent",
                    "request_received": pending_direction == "received",
                }
            )
    else:
        friend_ids = friend_repo.get_friend_ids(user.id)

    return templates.TemplateResponse(
        request=request,
        name="search_users.html",
        context={
            "user": user,
            "search_results": search_results,
            "query": q,
        },
    )


@router.post("/friend/add", name="add_friend")
async def add_friend(request: Request, user: AuthDep, db: SessionDep, friend_id: int = Form(...)):
    """Send a friend request"""
    user_repo = UserRepository(db)
    friend_repo = FriendRepository(db)

    friend = user_repo.get_by_id(friend_id)
    if not friend:
        flash(request, "User not found", "error")
        return RedirectResponse(url=request.url_for("search_users_view"), status_code=status.HTTP_302_FOUND)

    if friend_id == user.id:
        flash(request, "You cannot add yourself as a friend", "error")
        return RedirectResponse(url=request.url_for("search_users_view"), status_code=status.HTTP_302_FOUND)

    try:
        friend_repo.send_friend_request(user.id, friend_id)
        flash(request, f"Your friend request to {friend.username} is pending!", "success")
    except ValueError as e:
        flash(request, str(e), "warning")
    except Exception as e:
        flash(request, f"Error sending friend request: {str(e)}", "error")

    return RedirectResponse(url=request.url_for("search_users_view"), status_code=status.HTTP_302_FOUND)


@router.post("/friend/accept", name="accept_friend")
async def accept_friend(request: Request, user: AuthDep, db: SessionDep, request_id: int = Form(...)):
    """Accept a friend request"""
    friend_repo = FriendRepository(db)
    user_repo = UserRepository(db)

    try:
        friendship = friend_repo.accept_friend_request(request_id, user.id)
        requester = user_repo.get_by_id(friendship.user_id)
        name = requester.username if requester else "that user"
        flash(request, f"You are now friends with {name}!", "success")
    except ValueError as e:
        flash(request, str(e), "error")
    except Exception as e:
        flash(request, f"Error accepting request: {str(e)}", "error")

    return RedirectResponse(url=request.url_for("friends_view"), status_code=status.HTTP_302_FOUND)


@router.post("/friend/decline", name="decline_friend")
async def decline_friend(request: Request, user: AuthDep, db: SessionDep, request_id: int = Form(...)):
    """Decline or cancel a friend request"""
    friend_repo = FriendRepository(db)

    try:
        friend_repo.decline_friend_request(request_id, user.id)
        flash(request, "Friend request removed.", "info")
    except ValueError as e:
        flash(request, str(e), "error")
    except Exception as e:
        flash(request, f"Error declining request: {str(e)}", "error")

    return RedirectResponse(url=request.url_for("friends_view"), status_code=status.HTTP_302_FOUND)


@router.post("/friend/remove", name="remove_friend")
async def remove_friend(request: Request, user: AuthDep, db: SessionDep, friend_id: int = Form(...)):
    """Remove an accepted friend"""
    user_repo = UserRepository(db)
    friend_repo = FriendRepository(db)

    friend = user_repo.get_by_id(friend_id)
    if not friend:
        flash(request, "User not found", "error")
        return RedirectResponse(url=request.url_for("friends_view"), status_code=status.HTTP_302_FOUND)

    try:
        success = friend_repo.remove_friend(user.id, friend_id)
        if success:
            flash(request, f"Removed {friend.username} from friends", "success")
        else:
            flash(request, "You are not friends with this user", "info")
    except Exception as e:
        flash(request, f"Error removing friend: {str(e)}", "error")

    return RedirectResponse(url=request.url_for("friends_view"), status_code=status.HTTP_302_FOUND)


@router.get("/api/search-users", response_class=JSONResponse, name="api_search_users")
async def api_search_users(request: Request, user: AuthDep, db: SessionDep, q: str = ""):
    """API endpoint for searching users (for autocomplete)"""
    user_repo = UserRepository(db)
    friend_repo = FriendRepository(db)

    if not q or len(q) < 2:
        return {"results": []}

    search_results, _ = user_repo.search_users(q, page=1, limit=10)
    search_results = [u for u in search_results if u.id != user.id]

    friend_ids = friend_repo.get_friend_ids(user.id)

    results = [
        {
            "id": u.id,
            "username": u.username,
            "is_friend": u.id in friend_ids
        }
        for u in search_results
    ]

    return {"results": results}
