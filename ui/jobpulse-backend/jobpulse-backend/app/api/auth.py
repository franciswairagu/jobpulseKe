import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.google_auth import GoogleAuthUnavailable, verify_google_id_token
from app.core.security import create_access_token, create_refresh_token, decode_token, hash_password
from app.database import get_db
from app.models.user import Profile, User
from app.schemas.auth import RefreshRequest, TokenPair, UserOut

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _error(code: str, message: str, status_code: int):
    return HTTPException(status_code=status_code, detail={"error": {"code": code, "message": message, "details": {}}})


class GoogleLoginRequest(BaseModel):
    credential: str = Field(min_length=1, max_length=8192)


@router.get("/config")
def auth_config():
    return {"google_client_id": get_settings().GOOGLE_CLIENT_ID}


@router.post("/register", status_code=status.HTTP_410_GONE)
def register() -> None:
    raise _error("GOOGLE_SIGN_IN_REQUIRED", "Create your account with Google sign-in.", status.HTTP_410_GONE)


@router.post("/login", status_code=status.HTTP_410_GONE)
def login() -> None:
    raise _error("GOOGLE_SIGN_IN_REQUIRED", "Sign in with Google to continue.", status.HTTP_410_GONE)


@router.post("/google", response_model=TokenPair)
def google_login(payload: GoogleLoginRequest, db: Session = Depends(get_db)):
    settings = get_settings()
    if not settings.GOOGLE_CLIENT_ID:
        raise _error("GOOGLE_SIGN_IN_UNAVAILABLE", "Google sign-in is not configured.", status.HTTP_503_SERVICE_UNAVAILABLE)
    try:
        claims = verify_google_id_token(payload.credential, settings.GOOGLE_CLIENT_ID)
    except GoogleAuthUnavailable as exc:
        raise _error("GOOGLE_SIGN_IN_UNAVAILABLE", str(exc), status.HTTP_503_SERVICE_UNAVAILABLE)
    except ValueError:
        raise _error("INVALID_GOOGLE_CREDENTIAL", "Google sign-in could not be verified.", status.HTTP_401_UNAUTHORIZED)

    email = claims.get("email")
    subject = claims.get("sub")
    if not isinstance(email, str) or not email.strip() or not isinstance(subject, str) or not subject or claims.get("email_verified") is not True:
        raise _error("UNVERIFIED_GOOGLE_ACCOUNT", "Use a Google account with a verified email address.", status.HTTP_401_UNAUTHORIZED)

    email = email.strip().lower()
    user = db.query(User).filter(func.lower(User.email) == email).first()
    if user and not user.is_active:
        raise _error("ACCOUNT_INACTIVE", "This account has been deactivated.", status.HTTP_403_FORBIDDEN)
    if not user:
        user = User(email=email, hashed_password=hash_password(secrets.token_urlsafe(32)))
        db.add(user)
        db.flush()
        db.add(Profile(user_id=user.id, name=claims.get("name")))
    elif not user.profile:
        db.add(Profile(user_id=user.id, name=claims.get("name")))

    db.commit()
    db.refresh(user)

    claims = {"auth_provider": "google"}
    return TokenPair(
        access_token=create_access_token(str(user.id), claims),
        refresh_token=create_refresh_token(str(user.id), claims),
    )


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest, db: Session = Depends(get_db)):
    try:
        claims = decode_token(payload.refresh_token)
        if claims.get("type") != "refresh" or claims.get("auth_provider") != "google":
            raise ValueError("Not a refresh token")
        subject = uuid.UUID(claims.get("sub", ""))
    except (ValueError, TypeError):
        raise _error("INVALID_REFRESH_TOKEN", "Refresh token is invalid or expired.", status.HTTP_401_UNAUTHORIZED)

    user = db.query(User).filter(User.id == subject).first()
    if not user or not user.is_active:
        raise _error("INVALID_REFRESH_TOKEN", "Refresh token is invalid or expired.", status.HTTP_401_UNAUTHORIZED)
    return TokenPair(
        access_token=create_access_token(str(user.id), {"auth_provider": "google"}),
        refresh_token=create_refresh_token(str(user.id), {"auth_provider": "google"}),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout():
    # Stateless JWTs: logout is enforced client-side by discarding tokens.
    # For server-side revocation, add a Redis-backed token blacklist here.
    return None


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "is_active": current_user.is_active,
        "name": current_user.profile.name if current_user.profile else None,
    }
