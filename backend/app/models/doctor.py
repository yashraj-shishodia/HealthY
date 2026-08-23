import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Boolean, Integer, Text, Time, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.core.database import Base, UUIDType


class DoctorProfile(Base):
    __tablename__ = "doctor_profiles"

    id = Column(UUIDType, primary_key=True, default=uuid.uuid4)
    user_id = Column(UUIDType, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    specialisation = Column(String(100), index=True, nullable=False)
    bio = Column(Text, nullable=True)
    slot_duration_minutes = Column(Integer, default=30, nullable=False)
    timezone = Column(String(50), default="UTC", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    user = relationship("User", back_populates="doctor_profile")
    working_hours = relationship("DoctorWorkingHours", back_populates="doctor", cascade="all, delete-orphan")
    leaves = relationship("DoctorLeave", back_populates="doctor", cascade="all, delete-orphan")
    appointments = relationship("Appointment", back_populates="doctor", foreign_keys="Appointment.doctor_id")


class DoctorWorkingHours(Base):
    __tablename__ = "doctor_working_hours"

    id = Column(UUIDType, primary_key=True, default=uuid.uuid4)
    doctor_id = Column(UUIDType, ForeignKey("doctor_profiles.id", ondelete="CASCADE"), nullable=False)
    day_of_week = Column(Integer, nullable=False)  # 0=Monday ... 6=Sunday
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)

    __table_args__ = (
        UniqueConstraint("doctor_id", "day_of_week", "start_time", name="uq_doctor_working_hours_day_start"),
    )

    doctor = relationship("DoctorProfile", back_populates="working_hours")


class DoctorLeave(Base):
    __tablename__ = "doctor_leaves"

    id = Column(UUIDType, primary_key=True, default=uuid.uuid4)
    doctor_id = Column(UUIDType, ForeignKey("doctor_profiles.id", ondelete="CASCADE"), nullable=False)
    leave_date = Column(Date, nullable=False)
    reason = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        UniqueConstraint("doctor_id", "leave_date", name="uq_doctor_leave_date"),
    )

    doctor = relationship("DoctorProfile", back_populates="leaves")
