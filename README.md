# 🏥 Medical Booking System (Hệ thống Đặt lịch Khám bệnh)

Dự án xây dựng hệ thống quản lý đặt lịch khám bệnh trực tuyến, kết nối Bệnh nhân và Bác sĩ.
Hệ thống bao gồm API Backend (FastAPI) và Frontend (NextJS - đang phát triển).

## 🚀 Công nghệ sử dụng

**Backend:**
* **Ngôn ngữ:** Python 3.10+
* **Framework:** FastAPI
* **Database:** PostgreSQL
* **ORM:** SQLAlchemy
* **Authentication:** JWT (JSON Web Tokens), OAuth2
* **Password Hashing:** Argon2
* **Validation:** Pydantic

## 📂 Cấu trúc Dự án (Domain-Driven Design)

```text
BookingSystem/
├── backend/                # Mã nguồn Backend
│   ├── app/
│   │   ├── core/           # Cấu hình hệ thống (DB, Security)
│   │   ├── modules/        # Các chức năng nghiệp vụ (Auth, Doctors, Appointments...)
│   │   └── main.py         # File khởi chạy
│   ├── .env.example        # Mẫu biến môi trường
│   └── requirements.txt    # Danh sách thư viện
└── frontend/               # Mã nguồn Frontend (Coming soon)

## Hướng dẫn cài đặt 