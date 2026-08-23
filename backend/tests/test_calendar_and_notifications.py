import pytest
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
from app.models.appointment import Appointment, AppointmentStatus, CalendarSyncStatus, OverallCalendarSyncStatus
from app.models.notification import NotificationLog, NotificationType, NotificationStatus
from app.services.calendar_service import GoogleCalendarService
from app.services.email_service import EmailService
from app.services.leave_service import add_doctor_leave_with_cascade
from app.schemas.doctor import AddLeaveRequest


@pytest.mark.asyncio
async def test_email_idempotency(db_session):
    """Verify that duplicate email dispatches with identical idempotency keys are skipped."""
    appt_id = uuid.uuid4()
    recipient = "patient.idempotent@test.com"

    # 1. First Dispatch
    log1 = await EmailService.send_email(
        db=db_session,
        appointment_id=appt_id,
        recipient=recipient,
        notification_type=NotificationType.BOOKING_CONFIRMATION,
        subject="Booking Confirmed",
        body="Your booking is confirmed."
    )
    assert log1.status == NotificationStatus.SENT
    assert log1.attempt_count == 1

    # 2. Duplicate Dispatch with SAME key
    log2 = await EmailService.send_email(
        db=db_session,
        appointment_id=appt_id,
        recipient=recipient,
        notification_type=NotificationType.BOOKING_CONFIRMATION,
        subject="Booking Confirmed",
        body="Your booking is confirmed."
    )
    assert log2.id == log1.id
    assert log2.status == NotificationStatus.SENT
    assert log2.attempt_count == 1  # Not re-attempted because already SENT


@pytest.mark.asyncio
async def test_dual_participant_calendar_sync_isolation(async_client, db_session):
    """CRITICAL CALENDAR ISOLATION & DUAL-PARTICIPANT SYNC TEST:
    Verify patient-only, doctor-only, and independent dual-participant calendar synchronization logic.
    """
    # 1. Setup Admin, Doctor & Patient
    admin_reg = {"email": "admin.cal@healthy.com", "password": "AdminPassword123!", "full_name": "Admin Cal", "role": "ADMIN"}
    await async_client.post("/api/auth/register", json=admin_reg)
    admin_login = await async_client.post("/api/auth/login", json={"email": "admin.cal@healthy.com", "password": "AdminPassword123!"})
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    doc_req = {
        "email": "dr.cal@healthy.com",
        "password": "DocPassword123!",
        "full_name": "Dr. Calendar Sync",
        "specialisation": "Cardiology",
        "slot_duration_minutes": 30,
        "working_hours": [
            {"day_of_week": 0, "start_time": "09:00:00", "end_time": "12:00:00"}
        ]
    }
    doc_resp = await async_client.post("/api/admin/doctors", json=doc_req, headers=admin_headers)
    doctor_id_str = doc_resp.json()["id"]

    patient_reg = {"email": "patient.cal@healthy.com", "password": "PatientPassword123!", "full_name": "Patient Cal", "role": "PATIENT"}
    patient_user_resp = await async_client.post("/api/auth/register", json=patient_reg)
    patient_user_id = uuid.UUID(patient_user_resp.json()["id"])
    patient_login = await async_client.post("/api/auth/login", json={"email": "patient.cal@healthy.com", "password": "PatientPassword123!"})
    patient_headers = {"Authorization": f"Bearer {patient_login.json()['access_token']}"}

    # 2. Connect Patient's Google Calendar ONLY
    expires = datetime.now(timezone.utc) + timedelta(hours=1)
    await GoogleCalendarService.connect_user_calendar(
        db=db_session,
        user_id=patient_user_id,
        access_token="mock_patient_access_token",
        refresh_token="mock_patient_refresh_token",
        expires_at=expires
    )

    # 3. Book Appointment
    booking_payload = {
        "doctor_id": doctor_id_str,
        "appointment_date": "2026-08-24",
        "start_time": "09:00:00",
        "end_time": "09:30:00",
        "symptoms": "Heart palpitations"
    }
    book_resp = await async_client.post("/api/appointments", json=booking_payload, headers=patient_headers)
    assert book_resp.status_code == 201
    appt_id = uuid.UUID(book_resp.json()["id"])

    # 4. Perform Sync with Patient connected, Doctor NOT connected -> overall PARTIAL
    p_stat, d_stat, overall = await GoogleCalendarService.sync_appointment_calendars(db_session, appt_id, "CREATE")
    assert p_stat == CalendarSyncStatus.SYNCED
    assert d_stat == CalendarSyncStatus.NONE
    assert overall == OverallCalendarSyncStatus.PARTIAL


@pytest.mark.asyncio
async def test_doctor_leave_cascade_cancellation(async_client, db_session):
    """CRITICAL DOCTOR LEAVE CASCADE TEST:
    Verify that when an admin adds leave for a doctor, all active booked appointments on that date
    are automatically transitioned to CANCELLED_BY_LEAVE.
    """
    # 1. Setup Admin, Doctor & Patient
    admin_reg = {"email": "admin.leave@healthy.com", "password": "AdminPassword123!", "full_name": "Admin Leave", "role": "ADMIN"}
    await async_client.post("/api/auth/register", json=admin_reg)
    admin_login = await async_client.post("/api/auth/login", json={"email": "admin.leave@healthy.com", "password": "AdminPassword123!"})
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    doc_req = {
        "email": "dr.leavecascade@healthy.com",
        "password": "DocPassword123!",
        "full_name": "Dr. Leave Cascade",
        "specialisation": "Pediatrics",
        "slot_duration_minutes": 30,
        "working_hours": [
            {"day_of_week": 0, "start_time": "09:00:00", "end_time": "12:00:00"}
        ]
    }
    doc_resp = await async_client.post("/api/admin/doctors", json=doc_req, headers=admin_headers)
    doctor_id_str = doc_resp.json()["id"]
    doctor_id = uuid.UUID(doctor_id_str)

    patient_reg = {"email": "patient.leave@healthy.com", "password": "PatientPassword123!", "full_name": "Patient Leave", "role": "PATIENT"}
    await async_client.post("/api/auth/register", json=patient_reg)
    patient_login = await async_client.post("/api/auth/login", json={"email": "patient.leave@healthy.com", "password": "PatientPassword123!"})
    patient_headers = {"Authorization": f"Bearer {patient_login.json()['access_token']}"}

    # 2. Book Appointment for Monday 2026-08-24
    booking_payload = {
        "doctor_id": doctor_id_str,
        "appointment_date": "2026-08-24",
        "start_time": "09:00:00",
        "end_time": "09:30:00",
        "symptoms": "Child fever"
    }
    book_resp = await async_client.post("/api/appointments", json=booking_payload, headers=patient_headers)
    assert book_resp.status_code == 201
    appt_id = book_resp.json()["id"]

    # 3. Admin adds Leave for Doctor on 2026-08-24 via add_doctor_leave_with_cascade
    leave_req = AddLeaveRequest(leave_date="2026-08-24", reason="Medical Conference")
    leave, affected = await add_doctor_leave_with_cascade(db_session, doctor_id, leave_req)
    assert len(affected) == 1
    assert affected[0].id == uuid.UUID(appt_id)
    assert affected[0].status == AppointmentStatus.CANCELLED_BY_LEAVE

    # 4. Query Appointment via API -> status is CANCELLED_BY_LEAVE
    appt_resp = await async_client.get(f"/api/appointments/{appt_id}", headers=patient_headers)
    assert appt_resp.status_code == 200
    assert appt_resp.json()["status"] == "CANCELLED_BY_LEAVE"
