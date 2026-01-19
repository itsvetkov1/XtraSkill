"""
Authentication endpoints for OAuth 2.0 flows.

Provides initiate and callback endpoints for Google and Microsoft OAuth,
plus user info and logout endpoints.
"""

from typing import Dict

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.auth_service import OAuth2Service
from app.utils.jwt import create_access_token, get_current_user

router = APIRouter()

# In-memory state storage for CSRF protection
# TODO: Move to Redis in production for multi-instance deployments
_oauth_states: Dict[str, str] = {}


@router.post("/google/initiate")
async def google_oauth_initiate(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Initiate Google OAuth flow.

    Returns authorization URL for client to open in browser.
    State parameter stored for CSRF validation on callback.

    Returns:
        {"auth_url": "https://accounts.google.com/..."}
    """
    oauth_service = OAuth2Service(db)

    # Determine redirect URI based on platform
    # Web uses localhost:8080, mobile uses custom scheme
    redirect_uri = "http://localhost:8002/auth/google/callback"

    auth_url, state = await oauth_service.get_google_auth_url(redirect_uri)

    # Store state for validation on callback
    _oauth_states[state] = "google"

    return {"auth_url": auth_url, "state": state}


@router.get("/google/callback")
async def google_oauth_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Handle Google OAuth callback.

    Exchanges authorization code for user info, creates/updates user,
    generates JWT token, and redirects to Flutter app with token.

    Query params:
        code: Authorization code from Google
        state: State parameter for CSRF validation

    Redirects to:
        http://localhost:8080/auth/callback?token={jwt_token}
    """
    # Validate state parameter
    expected_provider = _oauth_states.get(state)
    if not expected_provider or expected_provider != "google":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter",
        )

    # Remove used state
    del _oauth_states[state]

    oauth_service = OAuth2Service(db)
    redirect_uri = "http://localhost:8002/auth/google/callback"

    try:
        # Process callback and get user
        user = await oauth_service.process_google_callback(
            code=code,
            state=state,
            expected_state=state,
            redirect_uri=redirect_uri,
        )

        # Generate JWT token
        token = create_access_token(user.id, user.email)

        # Redirect to Flutter app with token
        # Web: http://localhost:8080/auth/callback?token={token}
        # Mobile would use: com.baassistant://auth/callback?token={token}
        return RedirectResponse(
            url=f"http://localhost:8080/auth/callback?token={token}"
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth authentication failed",
        ) from e


@router.post("/microsoft/initiate")
async def microsoft_oauth_initiate(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Initiate Microsoft OAuth flow.

    Returns authorization URL for client to open in browser.
    State parameter stored for CSRF validation on callback.

    Returns:
        {"auth_url": "https://login.microsoftonline.com/..."}
    """
    oauth_service = OAuth2Service(db)

    redirect_uri = "http://localhost:8001/auth/microsoft/callback"

    auth_url, state = await oauth_service.get_microsoft_auth_url(redirect_uri)

    # Store state for validation on callback
    _oauth_states[state] = "microsoft"

    return {"auth_url": auth_url, "state": state}


@router.get("/microsoft/callback")
async def microsoft_oauth_callback(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Handle Microsoft OAuth callback.

    Exchanges authorization code for user info, creates/updates user,
    generates JWT token, and redirects to Flutter app with token.

    Query params:
        code: Authorization code from Microsoft
        state: State parameter for CSRF validation

    Redirects to:
        http://localhost:8080/auth/callback?token={jwt_token}
    """
    # Validate state parameter
    expected_provider = _oauth_states.get(state)
    if not expected_provider or expected_provider != "microsoft":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid state parameter",
        )

    # Remove used state
    del _oauth_states[state]

    oauth_service = OAuth2Service(db)
    redirect_uri = "http://localhost:8001/auth/microsoft/callback"

    try:
        # Process callback and get user
        user = await oauth_service.process_microsoft_callback(
            code=code,
            state=state,
            expected_state=state,
            redirect_uri=redirect_uri,
        )

        # Generate JWT token
        token = create_access_token(user.id, user.email)

        # Redirect to Flutter app with token
        return RedirectResponse(
            url=f"http://localhost:8080/auth/callback?token={token}"
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OAuth authentication failed",
        ) from e


@router.post("/logout")
async def logout():
    """
    Logout endpoint.

    Since JWT is stateless, logout is client-side (discard token).
    This endpoint exists for API consistency.

    Returns:
        {"message": "Logged out successfully"}
    """
    return {"message": "Logged out successfully"}


@router.get("/me")
async def get_current_user_info(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current authenticated user information.

    Requires valid JWT token in Authorization header.

    Returns:
        User object with id, email, oauth_provider
    """
    from sqlalchemy import select

    from app.models import User

    # Fetch full user object from database
    stmt = select(User).where(User.id == user["user_id"])
    result = await db.execute(stmt)
    user_obj = result.scalar_one_or_none()

    if not user_obj:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return {
        "id": user_obj.id,
        "email": user_obj.email,
        "oauth_provider": user_obj.oauth_provider.value,
        "created_at": user_obj.created_at.isoformat(),
    }
