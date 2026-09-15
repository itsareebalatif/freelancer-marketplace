import re
from typing import Optional

from pydantic import BaseModel, EmailStr, field_validator

from app.models.enums import UserRole

_SPECIAL_CHARACTERS = "!@#$%^&*()_+-=[]{}|;:'\",.<>/?`~\\"


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: UserRole

    @field_validator("role", mode="before")
    @classmethod
    def normalize_role(cls, value):
        return value.upper() if isinstance(value, str) else value

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, value: str) -> str:
        if len(value) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if not re.search(r"[A-Z]", value):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(char in _SPECIAL_CHARACTERS for char in value):
            raise ValueError("Password must contain at least one special character")
        return value


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    email: EmailStr
    role: UserRole
    full_name: Optional[str] = None
