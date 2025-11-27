from sqlalchemy import Column, String, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship
from app.core.model_base import BaseModel
from sqlalchemy.dialects.postgresql import UUID


class Doctor(BaseModel):
    __tablename__ = "doctors"

    # Lien ket voi bang users
    user_id = Column(UUID(as_uuid=True), ForeignKey(
        "users.id"), nullable=False, unique=True)

    specialty = Column(String(100), nullable=False)  # Chuyen khoa
    price_per_visit = Column(Float, nullable=False)  # Giá khám
    description = Column(String(500), nullable=True)  # Mô tả về bác sĩ
    is_active = Column(Boolean, default=True)  # Còn làm việc hay không

    # Tạo quan hệ ngược để truy vấn: Từ Doctor lấy thông tin User
    user = relationship("app.modules.auth.models.User",
                        backref="doctor_profile")
