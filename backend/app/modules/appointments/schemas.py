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
    reason: str = Field(..., max_length=255,
                        description="Mô tả triệu chứng, vấn đề đang gặp phải.")

# Bác sĩ cập nhật trạng thái


class AppointmentUpdateStatus(BaseModel):
    status: str = Field(...,
                        pattern="^(pending|confirmed|canceled|completed)$")
    doctor_note: Optional[str] = None

# Output: Trả về thông tin cuộc hẹn


class AppointmentResponse(BaseModel):
    id: UUID
    start_time: datetime
    end_time: datetime
    status: str
    reason: str
    doctor_note: Optional[str]

    # Nested Model: Trả về thông tin Bác sĩ để hiển thị tên
    doctor: DoctorResponse


class PaymentUpdate(BaseModel):
    payment_status: str = Field(..., pattern="^(paid|unpaid|refunded)$")


class AppointmentCancel(BaseModel):
    reason: Optional[str] = None


class Config:
    from_attributes = True
