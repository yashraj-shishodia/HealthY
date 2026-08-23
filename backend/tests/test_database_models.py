import pytest
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateTable, CreateIndex
from app.models import (
    Base, User, UserRole, DoctorProfile, DoctorWorkingHours, DoctorLeave,
    Appointment, AppointmentStatus, AISummaryStatus, NotificationLog,
    MedicationReminder, CalendarConnection
)


def test_models_metadata_compilation():
    """Verify all ORM models compile SQL DDL schemas cleanly."""
    tables = [
        User.__table__,
        DoctorProfile.__table__,
        DoctorWorkingHours.__table__,
        DoctorLeave.__table__,
        Appointment.__table__,
        NotificationLog.__table__,
        MedicationReminder.__table__,
        CalendarConnection.__table__,
    ]

    for table in tables:
        ddl = str(CreateTable(table).compile(dialect=postgresql.dialect()))
        assert "CREATE TABLE" in ddl
        assert table.name in ddl


def test_appointment_partial_unique_index_ddl():
    """Verify partial unique index for active appointment slots compiles correctly."""
    index_ddl = None
    for index in Appointment.__table__.indexes:
        if index.name == "uq_doctor_active_slot":
            index_ddl = str(CreateIndex(index).compile(dialect=postgresql.dialect()))

    assert index_ddl is not None
    assert "CREATE UNIQUE INDEX uq_doctor_active_slot" in index_ddl
    assert "doctor_id" in index_ddl
    assert "appointment_date" in index_ddl
    assert "start_time" in index_ddl
    assert "WHERE status IN ('HELD', 'BOOKED')" in index_ddl
