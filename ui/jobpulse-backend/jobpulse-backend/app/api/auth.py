from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.security import create_access_token, create_refresh_token, decode_token, hash_password, verify_password
from app.database import get_db
from app.models.user import Profile, User
from app.schemas.auth import RefreshRequest, TokenPair, UserOut, UserRegister

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _error(code: str, message: str, status_code: int):
    return HTTPException(status_code=status_code, detail={"error": {"code": code, "message": message, "details": {}}})


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(payload: UserRegister, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise _error("EMAIL_ALREADY_REGISTERED", "An account with this email already exists.", status.HTTP_409_CONFLICT)

    user = User(email=payload.email, hashed_password=hash_password(payload.password))
    db.add(user)
    db.flush()
    db.add(Profile(user_id=user.id, name=payload.name))
    db.commit()
    db.refresh(user)
    return user


@router.post("/login", response_model=TokenPair)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise _error("INVALID_CREDENTIALS", "Incorrect email or password.", status.HTTP_401_UNAUTHORIZED)
    if not user.is_active:
        raise _error("ACCOUNT_INACTIVE", "This account has been deactivated.", status.HTTP_403_FORBIDDEN)

    return TokenPair(
        access_token=create_access_token(str(user.id)),
        refresh_token=create_refresh_token(str(user.id)),
    )


@router.post("/refresh", response_model=TokenPair)
def refresh(payload: RefreshRequest):
    try:
        claims = decode_token(payload.refresh_token)
        if claims.get("type") != "refresh":
            raise ValueError("Not a refresh token")
    except ValueError:
        raise _error("INVALID_REFRESH_TOKEN", "Refresh token is invalid or expired.", status.HTTP_401_UNAUTHORIZED)

    subject = claims["sub"]
    return TokenPair(
        access_token=create_access_token(subject),
        refresh_token=create_refresh_token(subject),
    )


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout():
    # Stateless JWTs: logout is enforced client-side by discarding tokens.
    # For server-side revocation, add a Redis-backed token blacklist here.
    return None


@router.get("/me", response_model=UserOut)
def me(current_user: User = Depends(get_current_user)):
    return current_user
