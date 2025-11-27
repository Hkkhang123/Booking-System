from pydantic import BaseModel, Field
from uuid import UUID
from typing import Optional
from app.modules.auth.schemas import UserResponse

# Tạo hồ sơ bác sĩ


class DoctorCreate(BaseModel):
    user_id: UUID
    specialty: str = Field(..., max_length=100)
    price_per_visit: float = Field(..., gt=0)
    description: Optional[str] = Field(None, max_length=500)

# Output: trả về thông tin hồ sơ bác sĩ


class DoctorResponse(BaseModel):
    id: UUID
    specialty: str
    price_per_visit: float
    description: Optional[str]
    is_active: bool

    # Kỹ thuật Nested Model: Trả về luôn thông tin User (Tên, Email) bên trong
    user: UserResponse

    class Config:
        from_attributes = True
