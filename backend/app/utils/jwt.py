"""
JWT token utilities for authentication.

Provides JWT creation, verification, and FastAPI dependency injection for protected routes.
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import User

# JWT configuration
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 7

# Bearer token security scheme for FastAPI
security = HTTPBearer()


def create_access_token(user_id: str, email: str) -> str:
    """
    Create a JWT access token for authenticated user.

    Args:
        user_id: User's UUID as string
        email: User's email address

    Returns:
        Encoded JWT token string

    Token payload:
        - sub: user_id (subject)
        - email: user's email
        - exp: expiration timestamp (7 days from now)
        - iat: issued at timestamp
    """
    now = datetime.utcnow()
    expire = now + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)

    payload = {
        "sub": user_id,
        "email": email,
        "exp": expire,
        "iat": now,
    }

    token = jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)
    return token


def verify_token(token: str) -> dict:
    """
    Verify and decode JWT token.

    Args:
        token: JWT token string

    Returns:
        Decoded token payload

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from e


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> dict:
    """
    FastAPI dependency to get current authenticated user from JWT.

    Usage:
        @app.get("/protected")
        async def protected_route(user: dict = Depends(get_current_user)):
            user_id = user["user_id"]
            email = user["email"]

    Args:
        credentials: HTTP Bearer token from Authorization header

    Returns:
        Dictionary with user_id and email

    Raises:
        HTTPException: If token is missing, invalid, or expired
    """
    token = credentials.credentials
    payload = verify_token(token)

    user_id = payload.get("sub")
    email = payload.get("email")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    return {"user_id": user_id, "email": email}


async def get_admin_user(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    FastAPI dependency to verify current user has admin privileges.

    Usage:
        @router.get("/admin/logs")
        async def list_logs(admin: User = Depends(get_admin_user)):
            # Only admins reach here

    Args:
        user: Current authenticated user dict from get_current_user
        db: Database session

    Returns:
        User object with admin privileges

    Raises:
        HTTPException 403: If user lacks admin privileges
        HTTPException 404: If user not found in database
    """
    stmt = select(User).where(User.id == user["user_id"])
    result = await db.execute(stmt)
    user_obj = result.scalar_one_or_none()

    if not user_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if not user_obj.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )

    return user_obj
