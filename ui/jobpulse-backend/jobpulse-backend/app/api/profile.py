from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models.resume import Resume
from app.models.user import Profile, User
from app.schemas.profile import ProfileOut, ProfileUpdate, ResumeProfileOut

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("", response_model=ProfileOut)
def get_profile(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    profile = current_user.profile
    latest = (
        db.query(Resume)
        .filter(Resume.user_id == current_user.id)
        .order_by(Resume.uploaded_at.desc(), Resume.id.desc())
        .first()
    )
    return ProfileOut(
        id=current_user.id,
        email=current_user.email,
        name=profile.name if profile else None,
        country=profile.country if profile else None,
        city=profile.city if profile else None,
        career_interest=profile.career_interest if profile else None,
        years_experience=profile.years_experience if profile else None,
        preferred_work_mode=profile.preferred_work_mode if profile else None,
        latest_resume=(
            ResumeProfileOut(
                resume_id=latest.id,
                original_filename=latest.original_filename,
                status=latest.status.value,
                uploaded_at=latest.uploaded_at,
                available=bool(latest.storage_key),
            )
            if latest
            else None
        ),
    )


@router.patch("", response_model=ProfileOut)
def update_profile(
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    profile = current_user.profile
    if profile is None:
        profile = Profile(user_id=current_user.id)
        current_user.profile = profile
        db.add(profile)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)

    db.commit()
    db.refresh(current_user)
    return get_profile(db, current_user)
