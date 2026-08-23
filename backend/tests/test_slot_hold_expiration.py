import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch


@pytest.mark.asyncio
async def test_slot_hold_expiration_lifecycle(async_client):
    """SLOT HOLD EXPIRATION AUDIT TEST:
    1. Patient A holds slot -> 201 HELD.
    2. Patient B attempts to book held slot -> 409 SLOT_UNAVAILABLE.
    3. Time advances past hold_expires_at (5 minutes).
    4. Patient B attempts slot -> 201 Created (BOOKED).
    """
    # 1. Setup Admin & Doctor
    admin_reg = {"email": "admin.exp@healthy.com", "password": "AdminPassword123!", "full_name": "Admin Exp", "role": "ADMIN"}
    await async_client.post("/api/auth/register", json=admin_reg)
    admin_login = await async_client.post("/api/auth/login", json={"email": "admin.exp@healthy.com", "password": "AdminPassword123!"})
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    monday_date = "2026-08-24"
    doc_req = {
        "email": "dr.holdexp@healthy.com",
        "password": "DocPassword123!",
        "full_name": "Dr. Hold Expiration",
        "specialisation": "Endocrinology",
        "slot_duration_minutes": 30,
        "working_hours": [
            {"day_of_week": 0, "start_time": "11:00:00", "end_time": "13:00:00"}
        ]
    }
    doc_resp = await async_client.post("/api/admin/doctors", json=doc_req, headers=admin_headers)
    doctor_id = doc_resp.json()["id"]

    # 2. Register Patient A & Patient B
    await async_client.post("/api/auth/register", json={"email": "patA.exp@test.com", "password": "PassA123!", "full_name": "Patient Exp A", "role": "PATIENT"})
    loginA = await async_client.post("/api/auth/login", json={"email": "patA.exp@test.com", "password": "PassA123!"})
    headersA = {"Authorization": f"Bearer {loginA.json()['access_token']}"}

    await async_client.post("/api/auth/register", json={"email": "patB.exp@test.com", "password": "PassB123!", "full_name": "Patient Exp B", "role": "PATIENT"})
    loginB = await async_client.post("/api/auth/login", json={"email": "patB.exp@test.com", "password": "PassB123!"})
    headersB = {"Authorization": f"Bearer {loginB.json()['access_token']}"}

    hold_payload = {
        "doctor_id": doctor_id,
        "appointment_date": monday_date,
        "start_time": "11:00:00",
        "end_time": "11:30:00"
    }

    initial_time = datetime.now(timezone.utc)

    # Step 1: Patient A holds slot at initial_time
    with patch("app.services.booking_service.get_now_utc", return_value=initial_time), \
         patch("app.services.availability_service.get_now_utc", return_value=initial_time):
        hold_resp = await async_client.post("/api/appointments/hold", json=hold_payload, headers=headersA)
        assert hold_resp.status_code == 201

    # Step 2: Patient B attempts same slot 2 mins later -> 409 Conflict
    t_plus_2 = initial_time + timedelta(minutes=2)
    book_payload_B = {**hold_payload, "symptoms": "Hormone evaluation"}
    with patch("app.services.booking_service.get_now_utc", return_value=t_plus_2), \
         patch("app.services.availability_service.get_now_utc", return_value=t_plus_2):
        conflict_resp = await async_client.post("/api/appointments", json=book_payload_B, headers=headersB)
        assert conflict_resp.status_code == 409
        assert conflict_resp.json()["error"]["code"] == "SLOT_UNAVAILABLE"

    # Step 3 & 4: Advance time 10 mins later (past 5-min hold) -> Patient B succeeds with 201 Created
    t_plus_10 = initial_time + timedelta(minutes=10)
    with patch("app.services.booking_service.get_now_utc", return_value=t_plus_10), \
         patch("app.services.availability_service.get_now_utc", return_value=t_plus_10):
        success_resp = await async_client.post("/api/appointments", json=book_payload_B, headers=headersB)
        assert success_resp.status_code == 201, f"Expected 201, got {success_resp.status_code}: {success_resp.text}"
        assert success_resp.json()["status"] == "BOOKED"
