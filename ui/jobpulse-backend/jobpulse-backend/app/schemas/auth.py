import uuid

from pydantic import BaseModel, EmailStr


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserOut(BaseModel):
    id: uuid.UUID
    email: EmailStr
    is_active: bool
    name: str | None = None

    class Config:
        from_attributes = True
