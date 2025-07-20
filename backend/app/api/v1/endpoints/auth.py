from typing import Optional

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.config import Settings, get_settings
from app.db.session import get_db_session
from app.models.user import User as UserModel
from app.schemas.user import CSRFToken, RegistrationStatus, User, UserCreate
from app.security.auth import (
    REFRESH_TOKEN_COOKIE_NAME,
    clear_auth_cookies,
    create_access_token,
    create_auth_cookies,
    create_auth_cookies_with_csrf,
    create_csrf_token,
    get_refresh_token,
    revoke_refresh_token,
    rotate_refresh_token,
    set_refresh_token_cookie,
)
from app.services.oauth import OAuthService, get_oauth_service
from app.services.user import (
    authenticate_user,
    create_oauth_user,
    create_user,
    get_user_by_email,
)

router = APIRouter()

# Create limiter instance for rate limiting
limiter = Limiter(key_func=get_remote_address)


class GoogleLoginRequest(BaseModel):
    credential: str


@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: UserModel = Depends(get_current_user),
) -> User:
    """Get current authenticated user information."""
    return User.model_validate(current_user)


@router.get("/registration-status", response_model=RegistrationStatus)
async def get_registration_status(
    settings: Settings = Depends(get_settings),
) -> RegistrationStatus:
    """Check if new user registration is currently allowed."""
    return RegistrationStatus(
        allowed=settings.ALLOW_REGISTRATION,
        message=(
            None
            if settings.ALLOW_REGISTRATION
            else settings.REGISTRATION_DISABLED_MESSAGE
        ),
    )


@router.post("/register", response_model=User)
@limiter.limit("3/minute")
async def register_user(
    request: Request,
    user_create: UserCreate,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> User:
    """Register a new user account."""
    if not settings.ALLOW_REGISTRATION:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=settings.REGISTRATION_DISABLED_MESSAGE,
        )

    try:
        user = await create_user(db, user_create)
        # Ensure related role is loaded to prevent lazy-load during response serialization
        await db.refresh(user, attribute_names=["role"])
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists.",
        ) from e

    access_token = create_access_token(data={"sub": user.email})
    await create_auth_cookies_with_csrf(response, access_token, db, user)

    return User.model_validate(user)


@router.post("/login", response_model=User)
@limiter.limit("5/minute")
async def login_user(
    request: Request,
    response: Response,
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db_session),
) -> User:
    """Authenticate user and set auth cookies."""
    user = await authenticate_user(db, form_data.username, form_data.password)
    # Ensure role relationship is loaded before returning the user
    if user is not None:
        await db.refresh(user, attribute_names=["role"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is not active. Please contact an administrator.",
        )

    access_token = create_access_token(data={"sub": user.email})
    await create_auth_cookies_with_csrf(response, access_token, db, user)

    return User.model_validate(user)


@router.post("/refresh")
async def refresh_access_token(
    response: Response,
    refresh_token: Optional[str] = Cookie(None, alias=REFRESH_TOKEN_COOKIE_NAME),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Refresh the access token using a valid refresh token."""
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="No refresh token provided.",
        )

    token_obj = await get_refresh_token(db, refresh_token)

    if not token_obj or token_obj.is_revoked or token_obj.is_expired:
        clear_auth_cookies(response)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token.",
        )

    user = token_obj.user
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive or not found.",
        )

    new_refresh_token = await rotate_refresh_token(db, refresh_token, user)
    if not new_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Could not rotate refresh token.",
        )

    access_token = create_access_token(data={"sub": user.email})
    create_auth_cookies(response, access_token)
    set_refresh_token_cookie(response, new_refresh_token)

    # Also issue a new CSRF token
    csrf_token = create_csrf_token()
    settings = get_settings()
    response.set_cookie(
        key="csrf_token",
        value=csrf_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=False,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
    )

    return {"message": "Access token refreshed successfully."}


@router.post("/logout")
async def logout_user(
    response: Response,
    refresh_token: Optional[str] = Cookie(None, alias=REFRESH_TOKEN_COOKIE_NAME),
    db: AsyncSession = Depends(get_db_session),
) -> dict:
    """Logout user by revoking refresh token and clearing auth cookies."""
    if refresh_token:
        await revoke_refresh_token(db, refresh_token)

    clear_auth_cookies(response)
    return {"message": "Successfully logged out"}


@router.get("/csrf-token", response_model=CSRFToken)
async def get_csrf_token(
    response: Response, settings: Settings = Depends(get_settings)
) -> CSRFToken:
    """Generate and set a CSRF token."""
    token = create_csrf_token()
    response.set_cookie(
        key="csrf_token",
        value=token,
        max_age=60 * 60 * 2,
        httponly=False,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax",
    )
    return CSRFToken(token=token)


@router.post("/google", response_model=User)
@limiter.limit("5/minute")
async def google_oauth_callback(
    request_obj: Request,
    request: GoogleLoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
    oauth_service: OAuthService = Depends(get_oauth_service),
) -> User:
    """Handle Google OAuth login."""
    user_info = await oauth_service.verify_google_token(
        request.credential, settings.GOOGLE_OAUTH_CLIENT_ID
    )

    email = user_info.email
    user = await get_user_by_email(db, email)

    if user:
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is not active. Please contact an administrator.",
            )
    else:
        if not settings.ALLOW_REGISTRATION:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=settings.REGISTRATION_DISABLED_MESSAGE,
            )
        user = await create_oauth_user(db, email, "google")

    access_token = create_access_token(data={"sub": user.email})
    await create_auth_cookies_with_csrf(response, access_token, db, user)

    return User.model_validate(user)
