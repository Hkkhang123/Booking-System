from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, func
from datetime import datetime, timedelta, timezone
from typing import List
from uuid import UUID

from app.core.database import get_db
from app.modules.appointments import models, schemas
from app.modules.auth.dependencies import get_current_user, get_current_admin
from app.modules.auth.models import User
from app.modules.doctors.models import Doctor

router = APIRouter()

# Cấu hình: Mỗi ca tư vấn thường kéo dài 60p
APPOINTMENT_DURATION_MINUTES = 60

# API đặt lịch


@router.post("/", response_model=schemas.AppointmentResponse, status_code=status.HTTP_201_CREATED)
def create_appointment(booking_in: schemas.AppointmentCreate,
                       db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_user)):
    """
    Đặt lịch hẹn
    Logic:
    1. Kiểm tra bác sĩ có tồn tại không
    2. Tính giờ kết thúc (start + 60p)
    3. Check trùng lịch
    4. Lưu vào DB
    """

    # 1. Kiểm tra bác sĩ có tồn tại không
    doctor = db.query(Doctor).filter(Doctor.id == booking_in.doctor_id).first()
    if not doctor or not doctor.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Bác sĩ không tồn tại hoặc đang tạm nghỉ.")

    # 2. Tính toán thời gian

    start_time = booking_in.start_time  # datetime object

    if start_time.tzinfo is not None:
        # Nếu start_time chưa có timezone, gắn timezone UTC cho nó
        start_time = start_time.replace(tzinfo=timezone.utc)

    # Kiểm tra không được đặt lịch trong quá khứ
    if start_time < datetime.now(timezone.utc):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="Không thể đặt lịch trong quá khứ.")

    end_time = start_time + timedelta(minutes=APPOINTMENT_DURATION_MINUTES)

    # Check trùng lịch
    # Check 2 khoảng thời gian (A, B) và (C, D) có giao nhau không
    # (StartA < EndB) AND (EndA > StartB)

    overlapping_appointment = db.query(models.Appointment).filter(
        models.Appointment.doctor_id == booking_in.doctor_id,
        models.Appointment.status != "cancelled",
        and_(
            models.Appointment.start_time < end_time,
            models.Appointment.end_time > start_time
        )
    ).first()

    if overlapping_appointment:
        raise HTTPException(409, detail="Bác sĩ đã kín lịch khung giờ này")

    # Tạo lịch hẹn
    new_appointment = models.Appointment(
        patient_id=current_user.id,
        doctor_id=booking_in.doctor_id,
        start_time=start_time,
        end_time=end_time,
        reason=booking_in.reason,
        status="pending",  # Mặc định là pending
        paid_price=doctor.price_per_visit,
        doctor_note=None
    )

    db.add(new_appointment)
    db.commit()
    db.refresh(new_appointment)

    return new_appointment

# API lấy danh sách lịch hẹn


@router.get("/my-appointments", response_model=List[schemas.AppointmentResponse])
def get_my_appointments(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    API Đa năng:
    - Nếu là Bác sĩ -> Xem lịch mình CẦN KHÁM cho khách.
    - Nếu là Bệnh nhân -> Xem lịch mình ĐÃ ĐẶT.
    """
    # Khởi tạo query chung
    query = db.query(models.Appointment)

    # TRƯỜNG HỢP 1: LÀ BÁC SĨ
    if current_user.role == "doctor":
        # Tìm hồ sơ chuyên môn (Doctor Profile)
        doctor_profile = db.query(Doctor).filter(
            Doctor.user_id == current_user.id).first()

        if not doctor_profile:
            # Báo lỗi ngay nếu tài khoản bị lỗi (có role doctor nhưng không có trong bảng doctors)
            raise HTTPException(
                status_code=400,
                detail="Tài khoản Doctor này chưa có hồ sơ chuyên môn (Vui lòng liên hệ Admin)"
            )

        # Lọc các lịch mà bác sĩ này ĐƯỢC ĐẶT (theo doctor_id)
        appointments = query.filter(models.Appointment.doctor_id == doctor_profile.id)\
                            .order_by(models.Appointment.start_time.desc()).all()
        return appointments

    # TRƯỜNG HỢP 2: LÀ BỆNH NHÂN (HOẶC ADMIN)
    # Lọc các lịch mà user này ĐI ĐẶT (theo patient_id)
    appointments = query.filter(models.Appointment.patient_id == current_user.id)\
                        .order_by(models.Appointment.start_time.desc()).all()

    return appointments
# 2. API CẬP NHẬT LỊCH HẸN (DÀNH CHO BÁC SĨ)


@router.patch("/{appointment_id}/status", response_model=schemas.AppointmentResponse)
def update_appointment_status(
    appointment_id: str,
    status_update: schemas.AppointmentUpdateStatus,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    appt = db.query(models.Appointment).filter(
        models.Appointment.id == appointment_id).first()

    if not appt:
        raise HTTPException(404, "Lịch hẹn không tồn tại.")

    # Kiểm tra quyền: chỉ bác sĩ của lịch hẹn hoặc admin mới được phép thay đổi
    doctor_profile = db.query(Doctor).filter(
        Doctor.user_id == current_user.id).first()

    is_own_doctor = doctor_profile and doctor_profile.id == appt.doctor_id
    is_admin = current_user.role == "admin"

    if not is_own_doctor and not is_admin:
        raise HTTPException(403, "Bạn không có quyền thay đổi lịch hẹn này.")

    # Cập nhật
    appt.status = status_update.status
    if status_update.doctor_note is not None:
        appt.doctor_note = status_update.doctor_note

    db.commit()
    db.refresh(appt)
    return appt


# API Thống kê
@router.get("/stats/revenue", dependencies=[Depends(get_current_admin)])
def get_platform_revenue(
    start_date: datetime,
    end_date: datetime,
    db: Session = Depends(get_db)

):
    """
    Tính tổng doanh thu của toàn hệ thống trong khoảng thời gian.
    Chỉ tính các lịch đã HOÀN THÀNH (completed).
    """
    revenue = db.query(func.sum(models.Appointment.paid_price))\
        .filter(models.Appointment.status == "completed",
                models.Appointment.start_time >= start_date,
                models.Appointment.start_time <= end_date)\
        .scalar()  # scalar() để lấy ra con số duy nhất thay vì list

    return {
        "start_date": start_date,
        "end_date": end_date,
        "revenue": revenue or 0
    }

# Thống kê revenue cho bác sĩ


def get_my_income(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)

):
    # Tìm profile bác sĩ
    doctor = db.query(Doctor).filter(Doctor.user_id == current_user.id).first()
    if not doctor:
        raise HTTPException(400, "Bạn không phải là bác sĩ")

    income = db.query(func.sum(models.Appointment.paid_price)).filter(
        models.Appointment.doctor_id == doctor.id,
        models.Appointment.status == "completed"
    ).scalar()

    count = db.query(func.count(models.Appointment.id)).filter(
        models.Appointment.doctor_id == doctor.id,
        models.Appointment.status == "completed"
    ).scalar()

    return {
        "total_income": income or 0,
        "total_patient": count or 0
    }


@router.patch("/{appointment_id}/payment", response_model=schemas.AppointmentResponse)
def confirm_payment(
    appointment_id: UUID,
    payment_in: schemas.PaymentUpdate,
    db: Session = Depends(get_db),
    current_user:  User = Depends(get_current_user)
):
    appt = db.query(models.Appointment).filter(
        models.Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(404, "Không tìm thấy lịch.")

    # Check quyền
    doctor_profile = db.query(Doctor).filter(
        Doctor.user_id == current_user.id).first()
    is_owner = doctor_profile and doctor_profile.id == appt.doctor_id
    is_admin = current_user.role == "admin"

    if not (is_owner or is_admin):
        raise HTTPException(403, "Bạn không có quyền xác nhận thanh toán.")

    appt.payment_status = payment_in.payment_status
    db.commit()
    db.refresh(appt)
    return appt


@router.patch("/{appointment_id}/cancel", response_model=schemas.AppointmentResponse)
def cancel_my_appointment(
    appointment_id: UUID,
    cancel_in: schemas.AppointmentCancel,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Tìm lịch hẹn
    appt = db.query(models.Appointment).filter(
        models.Appointment.id == appointment_id).first()
    if not appt:
        raise HTTPException(404, "Lịch hẹn không tồn tại")

    # 2. Check quyền sở hữu (Bắt buộc phải là người đặt lịch mới được hủy)
    if appt.patient_id != current_user.id:
        raise HTTPException(
            403, "Bạn không có quyền hủy lịch hẹn của người khác")

    # 3. Check trạng thái
    if appt.status in ["completed", "cancelled"]:
        raise HTTPException(
            400, "Lịch hẹn này đã kết thúc hoặc đã hủy từ trước")

    # 4. CHECK THỜI GIAN (QUAN TRỌNG)
    # Lấy giờ hiện tại theo UTC để so sánh
    now = datetime.now(timezone.utc)

    time_diff = appt.start_time - now

    hours_until_appointment = time_diff.total_seconds() / 3600

    # Quá giờ khám -> chặn
    if hours_until_appointment < 0:
        raise HTTPException(400, "Không thể hủy lịch hẹn quá khứ")

    refund_msg = ""

    if appt.payment_status == "paid":

        # Hủy sớm trước 24h -> Hoàn 100%
        if hours_until_appointment >= 24:
            appt.payment_status = "refunded"
            appt.refund_amount = appt.paid_price
            refund_msg = f"Hoàn lại ({appt.paid_price:,.0f} VND)"

        # Hủy sát giờ -> Không hoàn tiền
        else:
            appt.refund_amount = 0
            refund_msg = "Hủy sát giờ, Không hoàn tiền"

    # 5. Thực hiện hủy
    appt.status = "cancelled"

    # Ghi lý do hủy vào (nối thêm vào reason cũ)
    cancel_reason = cancel_in.reason if cancel_in.reason else "Bệnh nhân tự hủy"
    appt.reason = f"{appt.reason} | [Đã hủy]: {cancel_reason}"

    db.commit()
    db.refresh(appt)
    return appt
