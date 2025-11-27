from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.modules.doctors import models, schemas
from app.modules.auth.models import User
from typing import Optional, List

router = APIRouter()

# API tạo bác sĩ


@router.post("/", response_model=schemas.DoctorResponse, status_code=status.HTTP_201_CREATED)
def create_doctor(doctor: schemas.DoctorCreate, db: Session = Depends(get_db)):
    # Kiểm tra user có tồn tại không
    user = db.query(User).filter(User.id == doctor.user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User không tồn tại")

    # Kiểm tra user đã là bác sĩ hay chưa
    existing_doctor = db.query(models.Doctor).filter(
        models.Doctor.user_id == doctor.user_id).first()
    if existing_doctor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="User đã là bác sĩ")

    # Tạo hồ sơ bác sĩ mới
    new_doctor = models.Doctor(
        user_id=doctor.user_id,
        specialty=doctor.specialty,
        price_per_visit=doctor.price_per_visit,
        description=doctor.description
    )

    # Cập nhật role user thành doctor
    user.role = "doctor"

    db.add(new_doctor)
    db.commit()
    db.refresh(new_doctor)
    return new_doctor

# API lấy thông tin bác sĩ theo ID


@router.get("/{doctor_id}", response_model=List[schemas.DoctorResponse])
def get_doctor(
    skip: int = 0,
    limit: int = 10,
    specialty: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db)
):
    # Lấy tất cả bác sĩ đang hoạt động
    query = db.query(models.Doctor).filter(models.Doctor.is_active == True)

    # Lọc theo chuyên khoa nếu có
    if specialty:
        query = query.filter(models.Doctor.specialty.ilike(f"%{specialty}%"))

    # Lọc theo từ khóa tìm kiếm
    if search:
        query = query.join(models.Doctor.user).filter(
            (models.Doctor.description.ilike(f"%{search}%")) |
            (User.name.ilike(f"%{search}%"))
        )

    doctors = query.offset(skip).limit(limit).all()
    return doctors

# API lấy danh sách các chuyên khoa


@router.get("/specialties", response_model=List[str])
def get_specialties(db: Session = Depends(get_db)):
    """
    API lấy danh sách các chuyên khoa để hiển thị lên Dropdown lọc
    """
    # Lấy các chuyên khoa duy nhất (Distinct) từ bảng Doctors
    specialties = db.query(models.Doctor.specialty).distinct().all()

    # Kết quả trả về của query là list các tuple [('Tim mạch',), ('Nha khoa',)]
    # Cần chuyển về list string đơn giản ['Tim mạch', 'Nha khoa']
    return [s[0] for s in specialties if s[0]]
