from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from datetime import datetime


class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=32)
    full_name: str = Field(..., min_length=2, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: UUID
    email: EmailStr
    full_name: Optional[str]
    role: str
    created_at: datetime

    class Config:
        from_attributes = True  # Cho pheps doc tu SQLAlchemy model


class Token(BaseModel):  # Schema tra ve token
    access_token: str
    token_type: str


class UserUpdateAdmin(BaseModel):
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    is_active: Optional[bool] = None  # Để khóa tài khoản
    role: Optional[str] = None  # Để phân quyền
