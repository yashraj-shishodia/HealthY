import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Text, Integer, DateTime, ForeignKey, Enum as SQLEnum
)
from sqlalchemy.orm import relationship
from app.core.database import Base, UUIDType


class NotificationType(str, enum.Enum):
    BOOKING_CONFIRMATION = "BOOKING_CONFIRMATION"
    APPOINTMENT_REMINDER = "APPOINTMENT_REMINDER"
    CANCELLATION = "CANCELLATION"
    LEAVE_CONFLICT = "LEAVE_CONFLICT"
    MEDICATION_REMINDER = "MEDICATION_REMINDER"


class NotificationStatus(str, enum.Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"


class ReminderStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class NotificationLog(Base):
    __tablename__ = "notification_logs"

    id = Column(UUIDType, primary_key=True, default=uuid.uuid4)
    idempotency_key = Column(String(255), unique=True, index=True, nullable=False)
    appointment_id = Column(UUIDType, ForeignKey("appointments.id", ondelete="CASCADE"), nullable=True, index=True)
    recipient = Column(String(255), nullable=False)
    notification_type = Column(SQLEnum(NotificationType), nullable=False)
    provider = Column(String(50), nullable=False, default="Mock")
    status = Column(SQLEnum(NotificationStatus), nullable=False, default=NotificationStatus.PENDING)
    attempt_count = Column(Integer, default=0, nullable=False)
    last_error = Column(Text, nullable=True)
    sent_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    appointment = relationship("Appointment", back_populates="notification_logs")


class MedicationReminder(Base):
    __tablename__ = "medication_reminders"

    id = Column(UUIDType, primary_key=True, default=uuid.uuid4)
    appointment_id = Column(UUIDType, ForeignKey("appointments.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(UUIDType, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    medication_name = Column(String(255), nullable=False)
    dosage = Column(String(100), nullable=False)
    frequency = Column(String(100), nullable=False)
    next_run_at = Column(DateTime(timezone=True), nullable=False, index=True)
    end_at = Column(DateTime(timezone=True), nullable=False)
    status = Column(SQLEnum(ReminderStatus), nullable=False, default=ReminderStatus.ACTIVE)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    appointment = relationship("Appointment", back_populates="medication_reminders")
    patient = relationship("User", back_populates="medication_reminders")
