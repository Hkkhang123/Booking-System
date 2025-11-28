from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime
from app.modules.auth.schemas import UserResponse
from app.modules.doctors.schemas import DoctorResponse

# Input: Bệnh nhân gửi lên


class AppointmentCreate(BaseModel):
    doctor_id: UUID
    start_time: datetime
    reason: Optional[str] = Field(None, max_length=255)

# Output: Trả về thông tin cuộc hẹn


class AppointmentResponse(BaseModel):
    id: UUID
    start_time: datetime
    end_time: datetime
    status: str
    reason: Optional[str]

    # Nested Model: Trả về thông tin Bác sĩ để hiển thị tên
    doctor: DoctorResponse


class Config:
    from_attributes = True
