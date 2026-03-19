# ============================================================
# api/routes/auth.py
# PURPOSE: Auth endpoints — login, register, user management
# ============================================================

from fastapi import APIRouter, HTTPException, Depends, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from datetime import datetime, timezone
from api.auth import (
    authenticate_user, create_access_token, hash_password,
    require_auth, require_admin, USERS_DB,
    Token, UserCreate, UserResponse
)

router = APIRouter()


@router.post("/login", response_model=Token,
             summary="Login — returns JWT Bearer token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Login with username and password to get a JWT token.

    **Default accounts:**
    | Username | Password | Role |
    |---|---|---|
    | admin | admin123 | Full access |
    | operator | operator123 | Read + Write |
    | viewer | viewer123 | Read only |

    Use the token in the Authorization header: `Bearer <token>`
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(
        data={"sub": user["username"], "role": user["role"]}
    )
    return Token(
        access_token=token,
        token_type="bearer",
        role=user["role"],
        username=user["username"]
    )


@router.get("/me", summary="Get current user profile")
async def get_me(current_user: dict = Depends(require_auth)):
    """Returns the currently authenticated user's profile and permissions."""
    username  = current_user["username"]
    user_data = USERS_DB.get(username, {})
    role      = current_user["role"]

    permissions = {
        "admin":    ["read", "write", "delete", "manage_users"],
        "operator": ["read", "write"],
        "viewer":   ["read"],
    }.get(role, ["read"])

    return {
        "username":    username,
        "role":        role,
        "permissions": permissions,
        "created_at":  user_data.get("created_at", ""),
    }


@router.post("/register", response_model=UserResponse,
             summary="Register new user (Admin only)")
async def register(
    user_data: UserCreate,
    current_user: dict = Depends(require_admin())
):
    """
    Register a new user. **Requires admin role.**

    Roles:
    - **admin** → full access (read, write, delete, manage_users)
    - **operator** → read + write access
    - **viewer** → read-only access
    """
    if user_data.username in USERS_DB:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Username '{user_data.username}' already exists"
        )
    if user_data.role not in ["admin", "operator", "viewer"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be one of: admin, operator, viewer"
        )
    if len(user_data.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )

    created_at = datetime.now(timezone.utc).isoformat()
    USERS_DB[user_data.username] = {
        "password_hash": hash_password(user_data.password),
        "role":          user_data.role,
        "created_at":    created_at
    }
    return UserResponse(
        username=user_data.username,
        role=user_data.role,
        created_at=created_at
    )


@router.get("/users", summary="List all users (Admin only)")
async def list_users(current_user: dict = Depends(require_admin())):
    """Returns all registered users. **Requires admin role.**"""
    return {
        "total": len(USERS_DB),
        "users": [
            {
                "username":   u,
                "role":       d["role"],
                "created_at": d.get("created_at", "")
            }
            for u, d in USERS_DB.items()
        ]
    }


@router.delete("/users/{username}",
               summary="Delete user (Admin only)")
async def delete_user(
    username: str,
    current_user: dict = Depends(require_admin())
):
    """Deletes a user account. **Requires admin role.**"""
    if username not in USERS_DB:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User '{username}' not found"
        )
    if username == current_user["username"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    del USERS_DB[username]
    return {"message": f"User '{username}' deleted successfully"}
