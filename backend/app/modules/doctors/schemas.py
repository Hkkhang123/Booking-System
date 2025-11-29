from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional
from app.modules.auth.schemas import UserResponse

# --- 1. SPECIALTY SCHEMAS ---


class SpecialtyCreate(BaseModel):
    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    target_audience: Optional[str] = None
    keywords: Optional[str] = None


class SpecialtyResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]

    target_audience: Optional[str]
    keywords: Optional[str]

    class Config:
        from_attributes = True

# --- 2. CÁC SCHEMA INPUT (ĐĂNG KÝ / TẠO) ---

# Dành cho Admin tạo thủ công


class DoctorCreateInternal(BaseModel):
    user_id: UUID
    specialty_id: UUID
    price_per_visit: Optional[float] = None
    level_id: Optional[str] = None
    description: Optional[str] = Field(None, max_length=500)

# Dành cho Bác sĩ tự đăng ký (Public)


class DoctorRegisterPublic(BaseModel):
    email: str
    password: str
    full_name: str
    phone_number: Optional[str] = None

    specialty_id: UUID
    description: Optional[str] = None

# Dành cho Admin duyệt và chốt giá


class DoctorApproveAdmin(BaseModel):
    price_per_visit: Optional[float] = None
    level_id: UUID
    is_active: bool = True


# --- LEVEL SCHEMA ---
class DoctorLevelCreate(BaseModel):
    name: str
    code: str
    base_price: float
    description: Optional[str] = None


class DoctorLevelResponse(BaseModel):
    id: UUID
    name: str
    base_price: float
    description: Optional[str]

    class Config:
        from_attributes = True


# --- 3. SCHEMA OUTPUT (HIỂN THỊ) ---


class DoctorResponse(BaseModel):
    id: UUID

    price_per_visit: Optional[float]
    level_info: Optional[DoctorLevelResponse] = None

    description: Optional[str]
    is_active: bool

    specialty_info: SpecialtyResponse

    user: UserResponse

    class Config:
        from_attributes = True
