import uuid
from sqlalchemy import Column, DateTime
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base


class BaseModel(Base):
    __abstract__ = True

    id = Column(UUID(as_uuid=True), primary_key=True,
                default=uuid.uuid4, index=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
