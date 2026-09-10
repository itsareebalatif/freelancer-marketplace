from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator

from app.models.enums import UserRole


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: UserRole

    @field_validator("role", mode="before")
    @classmethod
    def normalize_role(cls, value):
        return value.upper() if isinstance(value, str) else value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    email: EmailStr
    role: UserRole
    full_name: Optional[str] = None
