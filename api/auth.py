# ============================================================
# api/auth.py
# PURPOSE: JWT Authentication + Password Hashing + RBAC
# ============================================================

from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import os

SECRET_KEY = os.getenv("SECRET_KEY", "project71-secret-key-change-in-production")
ALGORITHM  = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context  = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)


class Token(BaseModel):
    access_token: str
    token_type:   str
    role:         str
    username:     str

class TokenData(BaseModel):
    username: Optional[str] = None
    role:     Optional[str] = None

class UserCreate(BaseModel):
    username: str
    password: str
    role:     str = "viewer"

class UserResponse(BaseModel):
    username:   str
    role:       str
    created_at: str


USERS_DB = {
    "admin": {
        "password_hash": pwd_context.hash("admin123"),
        "role":          "admin",
        "created_at":    "2026-01-01T00:00:00Z"
    },
    "operator": {
        "password_hash": pwd_context.hash("operator123"),
        "role":          "operator",
        "created_at":    "2026-01-01T00:00:00Z"
    },
    "viewer": {
        "password_hash": pwd_context.hash("viewer123"),
        "role":          "viewer",
        "created_at":    "2026-01-01T00:00:00Z"
    },
}

ROLE_PERMISSIONS = {
    "admin":    ["read", "write", "delete", "manage_users"],
    "operator": ["read", "write"],
    "viewer":   ["read"],
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def authenticate_user(username: str, password: str) -> Optional[dict]:
    user = USERS_DB.get(username)
    if not user:
        return None
    if not verify_password(password, user["password_hash"]):
        return None
    return {"username": username, **user}

def create_access_token(data: dict,
                        expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(token: Optional[str] = Depends(oauth2_scheme)):
    """Returns current user or None (for optional auth endpoints)."""
    if token is None:
        return None
    try:
        payload  = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        role     = payload.get("role")
        if username is None:
            return None
        return {"username": username, "role": role}
    except JWTError:
        return None


async def require_auth(token: Optional[str] = Depends(oauth2_scheme)):
    """Requires valid JWT — raises 401 if missing or invalid."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Login at POST /auth/login",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if token is None:
        raise credentials_exception
    try:
        payload  = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        role     = payload.get("role")
        if username is None:
            raise credentials_exception
        return {"username": username, "role": role}
    except JWTError:
        raise credentials_exception


def require_permission(permission: str):
    """Returns a dependency that checks for a specific permission."""
    async def check_permission(
        current_user: dict = Depends(require_auth)
    ):
        role    = current_user.get("role", "viewer")
        allowed = ROLE_PERMISSIONS.get(role, [])
        if permission not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{role}' does not have '{permission}' permission."
            )
        return current_user
    return check_permission


def require_admin():
    """Returns a dependency that requires admin role."""
    async def check_admin(current_user: dict = Depends(require_auth)):
        if current_user.get("role") != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin role required for this operation."
            )
        return current_user
    return check_admin