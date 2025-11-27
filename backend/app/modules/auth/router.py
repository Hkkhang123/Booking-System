from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.modules.auth import models, schemas
from app.core import security
from app.modules.auth.dependencies import get_current_user
from typing import List, Optional
from app.modules.auth.dependencies import get_current_user, get_current_admin

router = APIRouter()


@router.post("/register", response_model=schemas.UserResponse)
def register_user(user: schemas.UserRegister, db: Session = Depends(get_db)):
    # Kiem tra neu email da ton tai
    user_exist = db.query(models.User).filter(
        models.User.email == user.email).first()
    if user_exist:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email đã được sử dụng.")

    # Hash mat khau
    hashed_password = security.get_password_hash(user.password)

    # Tao user moi
    new_user = models.User(
        email=user.email,
        password=hashed_password,
        full_name=user.full_name,
        phone_number=user.phone_number
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@router.post("/login", response_model=schemas.Token)
def login_user(user_in: schemas.UserLogin, db: Session = Depends(get_db)):
    # Tim user
    user = db.query(models.User).filter(
        models.User.email == user_in.email).first()

    # Check mat khau
    if not user or not security.verify_password(user_in.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Email hoặc mật khẩu không đúng.")

    # Tao token
    access_token = security.create_access_token(data={"sub": str(user.id)})
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/logout")
def logout(current_user: models.User = Depends(get_current_user)):
    return {"message": "Đăng xuất thành công."}


@router.get("/users", response_model=List[schemas.UserResponse])
def get_users(
    skip: int = 0,
    limit: int = 10,
    search: Optional[str] = None,
    role: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_admin)
):
    query = db.query(models.User)

    # Lọc theo role
    if role:
        query = query.filter(models.User.role == role)

    # Lọc theo từ khóa tìm kiếm
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                models.User.full_name.ilike(search_term),
                models.User.email.ilike(search_term),
                models.User.phone_number.ilike(search_term)
            )
        )

    users = query.offset(skip).limit(limit).all()
    return users
