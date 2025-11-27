from sqlalchemy import Column, String, Boolean
from app.core.model_base import BaseModel


class User(BaseModel):
    __tablename__ = "users"

    email = Column(String(255), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    phone_number = Column(String(20), nullable=True)

    role = Column(String(20), default="patient")
    is_active = Column(Boolean, default=True)
