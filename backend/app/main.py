# app/main.py
from fastapi import FastAPI
from app.core.database import engine, Base
from app.modules.auth.router import router as auth_router
from app.modules.doctors.router import router as doctors_router
from app.modules.appointments.router import router as appointments_router
from app.modules.doctors import models as doctor_models
from app.modules.appointments import models as appointment_models
from app.modules.auth import models

# Tạo bảng trong DB dua tren model.py

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Booking System API")

app.include_router(auth_router, prefix="/auth", tags=["Authentication"])
app.include_router(doctors_router, prefix="/doctors", tags=["Doctors"])
app.include_router(appointments_router,
                   prefix="/appointments", tags=["Appointments"])


@app.get("/")
def health_check():
    return {"status": "ok", "message": "Booking System is running!"}
