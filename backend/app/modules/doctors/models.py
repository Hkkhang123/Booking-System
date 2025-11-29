from sqlalchemy import Column, String, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from app.core.model_base import BaseModel
from sqlalchemy.dialects.postgresql import UUID


class Specialty(BaseModel):
    __tablename__ = "specialties"

    name = Column(String(100), nullable=False, unique=True)  # Ten chuyen khoa
    description = Column(String(500), nullable=True)  # Mo ta chuyen khoa
    image = Column(String(255), nullable=True)  # Icon

    target_audience = Column(String(100), nullable=True)  # Đối tượng hướng đến

    keywords = Column(String(255), nullable=True)  # Từ khóa tìm kiếm

    # Quan hệ ngược
    doctors = relationship("Doctor", backref="specialty_info")


class Doctor(BaseModel):
    __tablename__ = "doctors"

    # Lien ket voi bang users
    user_id = Column(UUID(as_uuid=True), ForeignKey(
        "users.id"), nullable=False, unique=True)

    specialty_id = Column(UUID(as_uuid=True), ForeignKey(
        "specialties.id"), nullable=False)                  # Chuyen khoa

    price_per_visit = Column(Float, nullable=True)         # Giá khám

    # Trình độ chuyên môn
    level_id = Column(UUID(as_uuid=True), ForeignKey(
        "doctor_levels.id"), nullable=True)

    description = Column(String(500), nullable=True)        # Mô tả về bác sĩ

    # Mặc định là chưa duyệt
    is_active = Column(Boolean, default=False)

    # Tạo quan hệ ngược để truy vấn: Từ Doctor lấy thông tin User
    user = relationship("app.modules.auth.models.User",
                        backref="doctor_profile")


class DoctorLevel(BaseModel):
    __tablename__ = "doctor_levels"

    name = Column(String(50), nullable=False, unique=True)  # Tên cấp bậc
    code = Column(String(20), nullable=False, unique=True)  # Mã cấp bậc
    # Giá cơ bản cho cấp bậc
    base_price = Column(Float, nullable=False)

    description = Column(String(255), nullable=True)  # Mô tả cấp bậc

    doctors = relationship("Doctor", backref="level_info")
