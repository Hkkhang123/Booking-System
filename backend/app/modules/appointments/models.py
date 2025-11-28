from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.core.model_base import BaseModel
from sqlalchemy.dialects.postgresql import UUID


class Appointment(BaseModel):
    __tablename__ = "appointments"

    # Ai đặt ? (Liên kết với bảng users)
    patient_id = Column(UUID(as_uuid=True), ForeignKey(
        "users.id"), nullable=False)

    # Đặt ai ? (Liên kết với bảng doctors)
    doctor_id = Column(UUID(as_uuid=True), ForeignKey(
        "doctors.id"), nullable=False)

    # Thời gian
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)

    # Trạng thái và ghi chú
    # Trạng thái: pending, confirmed, canceled, completed
    status = Column(String(20), nullable=False, default="pending")
    reason = Column(String(255), nullable=True)  # Lý do khám

    # Quan hệ ngược để lấy thông tin chi tiết
    patient = relationship(
        "app.modules.auth.models.User", backref="appointments")
    doctor = relationship(
        "app.modules.doctors.models.Doctor", backref="appointments")
