from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
from typing import List

from app.core.database import get_db
from app.modules.appointments import models, schemas
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.models import User
from app.modules.doctors.models import Doctor

router = APIRouter()

# Cấu hình: Mỗi ca khám mặc định 30p
APPOINTMENT_DURATION_MINUTES = 30

# API đặt lịch khám


@router.post("/", response_model=schemas.AppointmentResponse, status_code=status.HTTP_201_CREATED)
def create_appointment(booking_in: schemas.AppointmentCreate,
                       db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_user)):
    """
    Đặt lịch khám
    Logic:
    1. Kiểm tra bác sĩ có tồn tại không
    2. Tính giờ kết thúc (start + 30p)
    3. Check trùng lịch
    4. Lưu vào DB
    """

    # 1. Kiểm tra bác sĩ có tồn tại không
    doctor = db.query(Doctor).filter(Doctor.id == booking_in.doctor_id).first()
    if not doctor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Bác sĩ không tồn tại.")

    if not doctor.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Bác sĩ đang tạm nghỉ.")

    # 2. Tính toán thời gian

    start_time = booking_in.start_time  # datetime object

    # Kiểm tra không được đặt lịch trong quá khứ
    if start_time < datetime.utcnow():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Không thể đặt lịch trong quá khứ.")

    end_time = start_time + timedelta(minutes=APPOINTMENT_DURATION_MINUTES)

    # Check trùng lịch
    # Check 2 khoảng thời gian (A, B) và (C, D) có giao nhau không
    # (StartA < EndB) AND (EndA > StartB)

    overlapping_appointment = db.query(models.Appointment).filter(
        models.Appointment.doctor_id == booking_in.doctor_id,
        models.Appointment.status != "canceled",
        and_(
            models.Appointment.start_time < end_time,
            models.Appointment.end_time > start_time
        )
    ).first()

    if overlapping_appointment:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Bác sĩ đã có lịch khám trong khung giờ này. Vui lòng chọn thời gian khác.")

    # Tạo lịch hẹn
    new_appointment = models.Appointment(
        patient_id=current_user.id,
        doctor_id=booking_in.doctor_id,
        start_time=start_time,
        end_time=end_time,
        reason=booking_in.reason,
        status="pending"  # Mặc định là pending
    )

    db.add(new_appointment)
    db.commit()
    db.refresh(new_appointment)

    return new_appointment

# API lấy danh sách lịch hẹn của chính mình (Bệnh nhân)


@router.get("/my-appointments", response_model=List[schemas.AppointmentResponse])
def get_my_appointments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    appointments = db.query(models.Appointment).filter(
        models.Appointment.patient_id == current_user.id)\
        .order_by(models.Appointment.start_time.desc())\
        .all()

    return appointments
