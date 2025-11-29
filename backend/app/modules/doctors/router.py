from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from uuid import UUID

from app.core.database import get_db
from app.modules.doctors import schemas
from app.modules.doctors.models import Doctor, Specialty, DoctorLevel
from app.modules.auth.models import User
from app.modules.auth.dependencies import get_current_admin
from app.core import security

router = APIRouter()

# ==========================================
# PHẦN 1: QUẢN LÝ CHUYÊN NGÀNH (SPECIALTY)
# ==========================================


@router.post("/specialties", response_model=schemas.SpecialtyResponse, status_code=status.HTTP_201_CREATED)
def create_specialty(
    specialty_in: schemas.SpecialtyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)  # Chỉ Admin
):
    if db.query(Specialty).filter(Specialty.name == specialty_in.name).first():
        raise HTTPException(
            status_code=400, detail="Chuyên ngành này đã tồn tại")

    new_specialty = Specialty(name=specialty_in.name,
                              description=specialty_in.description,
                              target_audience=specialty_in.target_audience,
                              keywords=specialty_in.keywords)
    db.add(new_specialty)
    db.commit()
    db.refresh(new_specialty)
    return new_specialty


@router.get("/specialties", response_model=List[schemas.SpecialtyResponse])
def get_all_specialties(db: Session = Depends(get_db)):
    return db.query(Specialty).all()

# --- API QUẢN LÝ LEVEL ---


@router.post("/levels", response_model=schemas.DoctorLevelResponse, status_code=status.HTTP_201_CREATED)
def create_doctor_level(
    level_in: schemas.DoctorLevelCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    level = DoctorLevel(
        name=level_in.name,
        code=level_in.code,
        base_price=level_in.base_price,
        description=level_in.description
    )
    db.add(level)
    db.commit()
    db.refresh(level)
    return level


@router.get("/levels", response_model=List[schemas.DoctorLevelResponse])
def get_all_doctor_levels(db: Session = Depends(get_db)):
    return db.query(DoctorLevel).all()


# ==========================================
# PHẦN 2: BÁC SĨ ĐĂNG KÝ (PUBLIC)
# ==========================================


@router.post("/register", response_model=schemas.DoctorResponse)
def register_doctor_public(
    doctor_in: schemas.DoctorRegisterPublic,  # Schema nhập full từ A-Z
    db: Session = Depends(get_db)
):
    """
    Dành cho bác sĩ tự đăng ký tài khoản mới.
    Mặc định: Giá = NULL, Level = NULL, Trạng thái = Chờ duyệt.
    """
    # 1. Check User tồn tại
    if db.query(User).filter(User.email == doctor_in.email).first():
        raise HTTPException(status_code=400, detail="Email đã được sử dụng")

    # 2. Check Chuyên ngành
    if not db.query(Specialty).filter(Specialty.id == doctor_in.specialty_id).first():
        raise HTTPException(
            status_code=404, detail="Chuyên ngành không tồn tại")

    try:
        # 3. Tạo User (Role Doctor, inactive)
        hashed_password = security.get_password_hash(doctor_in.password)
        new_user = User(
            email=doctor_in.email,
            password=hashed_password,
            full_name=doctor_in.full_name,
            phone_number=doctor_in.phone_number,
            role="doctor",
            is_active=False
        )
        db.add(new_user)
        db.flush()

        # 4. Tạo Doctor Profile
        new_doctor = Doctor(
            user_id=new_user.id,
            specialty_id=doctor_in.specialty_id,
            description=doctor_in.description,
            price_per_visit=None,
            level_id=None,
            is_active=False
        )
        db.add(new_doctor)
        db.commit()
        db.refresh(new_doctor)
        return new_doctor

    except Exception as e:
        db.rollback()
        print(f"Lỗi: {e}")
        raise HTTPException(status_code=500, detail="Lỗi hệ thống")

# ==========================================
# PHẦN 3: QUẢN LÝ BÁC SĨ (ADMIN ONLY)
# ==========================================

# Nâng cấp User thành Bác sĩ, dùng trong trường hợp Admin muốn tạo bác sĩ từ User có sẵn


@router.post("/promote", response_model=schemas.DoctorResponse)
def promote_user_to_doctor(
    doctor_in: schemas.DoctorCreateInternal,  # Schema chỉ cần user_id
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Dành cho Admin: Biến một User cũ thành Bác sĩ.
    """
    user = db.query(User).filter(User.id == doctor_in.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User không tồn tại")

    if db.query(Doctor).filter(Doctor.user_id == doctor_in.user_id).first():
        raise HTTPException(
            status_code=400, detail="User này đã là bác sĩ rồi")

    new_doctor = Doctor(
        user_id=doctor_in.user_id,
        specialty_id=doctor_in.specialty_id,
        price_per_visit=doctor_in.price_per_visit,  # Admin có thể nhập giá luôn
        level_id=doctor_in.level_id,                     # Admin có thể nhập level luôn
        description=doctor_in.description,
        is_active=True  # Admin tạo thì cho active luôn
    )

    user.role = "doctor"
    db.add(new_doctor)
    db.commit()
    db.refresh(new_doctor)
    return new_doctor


@router.put("/{doctor_id}/approve", response_model=schemas.DoctorResponse)
def approve_doctor(
    doctor_id: UUID,
    approve_data: schemas.DoctorApproveAdmin,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_admin)
):
    """
    Dành cho Admin: Duyệt hồ sơ, chốt giá và cấp bậc.
    """
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        raise HTTPException(status_code=404, detail="Không tìm thấy bác sĩ")

    level_data = db.query(DoctorLevel).filter(
        DoctorLevel.id == approve_data.level_id).first()
    if not level_data:
        raise HTTPException(status_code=404, detail="Cấp bậc không tồn tại")

    final_price = approve_data.price_per_visit

    if final_price is None or final_price == 0:
        final_price = level_data.base_price

    # Update thông tin
    doctor.price_per_visit = final_price
    doctor.is_active = approve_data.is_active
    doctor.level_id = approve_data.level_id

    # Mở khóa user
    user = db.query(User).filter(User.id == doctor.user_id).first()
    if user:
        user.is_active = approve_data.is_active

    db.commit()
    db.refresh(doctor)
    return doctor

# ==========================================
# PHẦN 4: LẤY DANH SÁCH (PUBLIC)
# ==========================================


@router.get("/", response_model=List[schemas.DoctorResponse])
def get_doctors(
    skip: int = 0,
    limit: int = 10,
    specialty_name: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Doctor).filter(Doctor.is_active == True)

    if specialty_name:
        query = query.join(Doctor.specialty_info).filter(
            Specialty.name.ilike(f"%{specialty_name}%")
        )

    doctors = query.offset(skip).limit(limit).all()
    return doctors
