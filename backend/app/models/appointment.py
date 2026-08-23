import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Text, Date, Time, DateTime, ForeignKey, Enum as SQLEnum, Index, JSON
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from app.core.database import Base, UUIDType

JSONType = JSONB().with_variant(JSON(), "sqlite")


class AppointmentStatus(str, enum.Enum):
    HELD = "HELD"
    BOOKED = "BOOKED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    RESCHEDULED = "RESCHEDULED"
    CANCELLED_BY_LEAVE = "CANCELLED_BY_LEAVE"


class AISummaryStatus(str, enum.Enum):
    NOT_STARTED = "NOT_STARTED"
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class UrgencyLevel(str, enum.Enum):
    Low = "Low"
    Medium = "Medium"
    High = "High"


class CalendarSyncStatus(str, enum.Enum):
    NONE = "NONE"
    PENDING = "PENDING"
    SYNCED = "SYNCED"
    FAILED = "FAILED"


class OverallCalendarSyncStatus(str, enum.Enum):
    NOT_CONNECTED = "NOT_CONNECTED"
    PENDING = "PENDING"
    SYNCED = "SYNCED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(UUIDType, primary_key=True, default=uuid.uuid4)
    doctor_id = Column(UUIDType, ForeignKey("doctor_profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_id = Column(UUIDType, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    appointment_date = Column(Date, nullable=False, index=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    
    status = Column(SQLEnum(AppointmentStatus), nullable=False, default=AppointmentStatus.HELD, index=True)
    hold_expires_at = Column(DateTime(timezone=True), nullable=True, index=True)

    # Symptom & AI Pre-visit Summary Fields
    symptoms = Column(Text, nullable=True)
    pre_visit_summary = Column(Text, nullable=True)
    pre_visit_summary_status = Column(SQLEnum(AISummaryStatus), nullable=False, default=AISummaryStatus.NOT_STARTED)
    pre_visit_summary_error = Column(Text, nullable=True)
    urgency = Column(SQLEnum(UrgencyLevel), nullable=True)
    chief_complaint = Column(Text, nullable=True)
    suggested_questions = Column(JSONType, nullable=True)

    # Clinical Notes, Prescription & Post-visit Summary Fields
    doctor_notes = Column(Text, nullable=True)
    prescription = Column(Text, nullable=True)
    post_visit_summary = Column(JSONType, nullable=True)
    post_visit_summary_status = Column(SQLEnum(AISummaryStatus), nullable=False, default=AISummaryStatus.NOT_STARTED)
    post_visit_summary_error = Column(Text, nullable=True)

    # Google Calendar Independent Synchronization Fields
    patient_calendar_event_id = Column(String(255), nullable=True)
    doctor_calendar_event_id = Column(String(255), nullable=True)
    patient_calendar_sync_status = Column(SQLEnum(CalendarSyncStatus), nullable=False, default=CalendarSyncStatus.NONE)
    doctor_calendar_sync_status = Column(SQLEnum(CalendarSyncStatus), nullable=False, default=CalendarSyncStatus.NONE)
    overall_calendar_sync_status = Column(SQLEnum(OverallCalendarSyncStatus), nullable=False, default=OverallCalendarSyncStatus.NOT_CONNECTED)

    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    doctor = relationship("DoctorProfile", back_populates="appointments", foreign_keys=[doctor_id])
    patient = relationship("User", back_populates="patient_appointments", foreign_keys=[patient_id])
    notification_logs = relationship("NotificationLog", back_populates="appointment", cascade="all, delete-orphan")
    medication_reminders = relationship("MedicationReminder", back_populates="appointment", cascade="all, delete-orphan")

    __table_args__ = (
        Index(
            "uq_doctor_active_slot",
            "doctor_id",
            "appointment_date",
            "start_time",
            unique=True,
            postgresql_where=(status.in_([AppointmentStatus.HELD, AppointmentStatus.BOOKED])),
            sqlite_where=(status.in_([AppointmentStatus.HELD, AppointmentStatus.BOOKED])),
        ),
    )
