from fastapi import APIRouter, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi import status

from app.dependencies.auth import AuthDep
from app.dependencies.session import SessionDep
from app.repositories.friend import FriendRepository
from app.repositories.user import UserRepository
from app.services.friend_service import FriendService
from app.utilities.flash import flash
from app.routers import templates

router = APIRouter()


@router.get("/friends", response_class=HTMLResponse, name="friends_view")
async def friends_view(request: Request, user: AuthDep, db: SessionDep):
    """View all friends"""
    friend_repo = FriendRepository(db)
    user_repo = UserRepository(db)
    
    friends_rel = friend_repo.get_friends(user.id)
    friends = [user_repo.get_by_id(f.friend_id) for f in friends_rel]
    
    return templates.TemplateResponse(
        request=request,
        name="friends.html",
        context={
            "user": user,
            "friends": friends,
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
        search_results = [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "is_friend": u.id in friend_ids,
            }
            for u in results
        ]
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
    """Add a friend"""
    user_repo = UserRepository(db)
    friend_repo = FriendRepository(db)
    
    #  friend exists and is not the current user
    friend = user_repo.get_by_id(friend_id)
    if not friend:
        flash(request, "User not found", "error")
        return RedirectResponse(url=request.url_for("search_users_view"), status_code=status.HTTP_302_FOUND)
    
    if friend_id == user.id:
        flash(request, "You cannot add yourself as a friend", "error")
        return RedirectResponse(url=request.url_for("search_users_view"), status_code=status.HTTP_302_FOUND)
    
    try:
        friend_repo.add_friend(user.id, friend_id)
        flash(request, f"Added {friend.username} as a friend!", "success")
    except ValueError as e:
        flash(request, str(e), "error")
    except Exception as e:
        flash(request, f"Error adding friend: {str(e)}", "error")
    
    return RedirectResponse(url=request.url_for("search_users_view"), status_code=status.HTTP_302_FOUND)


@router.post("/friend/remove", name="remove_friend")
async def remove_friend(request: Request, user: AuthDep, db: SessionDep, friend_id: int = Form(...)):
    """Remove a friend"""
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
