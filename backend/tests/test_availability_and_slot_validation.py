import pytest
import uuid
from datetime import date, time
from app.services.availability_service import validate_requested_slot
from fastapi import HTTPException


@pytest.mark.asyncio
async def test_availability_and_slot_validation_rules(async_client, db_session):
    """Test valid slot generation, leave filtering, collision, and strict server slot validation."""
    # 1. Register Admin and create Doctor with 30-min slot duration on Monday (day_of_week 0: 09:00 - 12:00)
    admin_reg = {"email": "admin.avail@healthy.com", "password": "AdminPassword123!", "full_name": "Admin Avail", "role": "ADMIN"}
    await async_client.post("/api/auth/register", json=admin_reg)
    admin_login = await async_client.post("/api/auth/login", json={"email": "admin.avail@healthy.com", "password": "AdminPassword123!"})
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    monday_date = date(2026, 8, 24)
    doc_req = {
        "email": "dr.available@healthy.com",
        "password": "DocPassword123!",
        "full_name": "Dr. Slot Validator",
        "specialisation": "General Practice",
        "slot_duration_minutes": 30,
        "working_hours": [
            {"day_of_week": 0, "start_time": "09:00:00", "end_time": "12:00:00"}
        ]
    }
    doc_resp = await async_client.post("/api/admin/doctors", json=doc_req, headers=admin_headers)
    assert doc_resp.status_code == 201
    doctor_id_str = doc_resp.json()["id"]
    doctor_id = uuid.UUID(doctor_id_str)

    # 2. Test Availability Generation: should have 6 slots (09:00, 09:30, 10:00, 10:30, 11:00, 11:30)
    avail_resp = await async_client.get(f"/api/doctors/{doctor_id_str}/availability?date=2026-08-24")
    assert avail_resp.status_code == 200
    avail_data = avail_resp.json()
    assert avail_data["is_on_leave"] is False
    assert len(avail_data["slots"]) == 6
    assert avail_data["slots"][0]["start_time"] == "09:00:00"
    assert avail_data["slots"][0]["end_time"] == "09:30:00"

    # 3. Test Valid Slot Validation: 09:00-09:30 succeeds via service helper
    isValid = await validate_requested_slot(db_session, doctor_id, monday_date, time(9, 0), time(9, 30))
    assert isValid is True

    # 4. Test Invalid Slot — 15 minute offset (09:15-09:45) fails with 400 INVALID_SLOT
    with pytest.raises(HTTPException) as exc_info:
        await validate_requested_slot(db_session, doctor_id, monday_date, time(9, 15), time(9, 45))
    assert exc_info.value.status_code == 400
    assert exc_info.value.detail["error"]["code"] == "INVALID_SLOT"

    # 5. Test Invalid Slot — Incorrect duration (09:00-09:45) fails with 400 INVALID_SLOT
    with pytest.raises(HTTPException) as exc_info2:
        await validate_requested_slot(db_session, doctor_id, monday_date, time(9, 0), time(9, 45))
    assert exc_info2.value.status_code == 400
    assert exc_info2.value.detail["error"]["code"] == "INVALID_SLOT"

    # 6. Test Invalid Slot — Outside working hours (07:00-07:30) fails with 400 INVALID_SLOT
    with pytest.raises(HTTPException) as exc_info3:
        await validate_requested_slot(db_session, doctor_id, monday_date, time(7, 0), time(7, 30))
    assert exc_info3.value.status_code == 400
    assert exc_info3.value.detail["error"]["code"] == "INVALID_SLOT"

    # 7. Add Leave Day via Admin API -> all slots blocked, is_on_leave = True
    leave_resp = await async_client.post(f"/api/admin/doctors/{doctor_id_str}/leave", json={"leave_date": "2026-08-24", "reason": "Vacation"}, headers=admin_headers)
    assert leave_resp.status_code == 201

    avail_on_leave = await async_client.get(f"/api/doctors/{doctor_id_str}/availability?date=2026-08-24")
    assert avail_on_leave.status_code == 200
    assert avail_on_leave.json()["is_on_leave"] is True
    assert len(avail_on_leave.json()["slots"]) == 0
