import pytest
import asyncio


@pytest.mark.asyncio
async def test_simultaneous_parallel_booking_race_condition_returns_409(async_client):
    """CRITICAL TRUE PARALLEL CONCURRENCY EVALUATION TEST:
    Simultaneously dispatch parallel HTTP booking requests for Patient A and Patient B for the exact same slot.
    Verify:
    1. Exactly ONE request receives 201 Created.
    2. The simultaneous parallel request receives 409 Conflict (SLOT_UNAVAILABLE).
    3. Winner payload contains status=BOOKED.
    """
    # 1. Setup Admin & Doctor via API
    admin_reg = {"email": "admin.race@healthy.com", "password": "AdminPassword123!", "full_name": "Admin Race", "role": "ADMIN"}
    await async_client.post("/api/auth/register", json=admin_reg)
    admin_login = await async_client.post("/api/auth/login", json={"email": "admin.race@healthy.com", "password": "AdminPassword123!"})
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    monday_date = "2026-08-24"
    doc_req = {
        "email": "dr.raceparallel@healthy.com",
        "password": "DocPassword123!",
        "full_name": "Dr. Parallel Race",
        "specialisation": "Neurology",
        "slot_duration_minutes": 30,
        "working_hours": [
            {"day_of_week": 0, "start_time": "09:00:00", "end_time": "12:00:00"}
        ]
    }
    doc_resp = await async_client.post("/api/admin/doctors", json=doc_req, headers=admin_headers)
    assert doc_resp.status_code == 201
    doctor_id = doc_resp.json()["id"]

    # 2. Register Patient A & B
    await async_client.post("/api/auth/register", json={"email": "parallelA@test.com", "password": "PassA123!", "full_name": "Patient Parallel A", "role": "PATIENT"})
    loginA = await async_client.post("/api/auth/login", json={"email": "parallelA@test.com", "password": "PassA123!"})
    headersA = {"Authorization": f"Bearer {loginA.json()['access_token']}"}

    await async_client.post("/api/auth/register", json={"email": "parallelB@test.com", "password": "PassB123!", "full_name": "Patient Parallel B", "role": "PATIENT"})
    loginB = await async_client.post("/api/auth/login", json={"email": "parallelB@test.com", "password": "PassB123!"})
    headersB = {"Authorization": f"Bearer {loginB.json()['access_token']}"}

    booking_payload = {
        "doctor_id": doctor_id,
        "appointment_date": monday_date,
        "start_time": "09:00:00",
        "end_time": "09:30:00",
        "symptoms": "Parallel race condition test"
    }

    # 3. Simultaneously fire parallel requests with asyncio.gather
    req_A = async_client.post("/api/appointments", json=booking_payload, headers=headersA)
    req_B = async_client.post("/api/appointments", json=booking_payload, headers=headersB)

    resp_A, resp_B = await asyncio.gather(req_A, req_B)

    status_codes = [resp_A.status_code, resp_B.status_code]
    assert 201 in status_codes, f"Expected one 201 Created, got {status_codes}"
    assert 409 in status_codes, f"Expected one 409 Conflict, got {status_codes}"

    winner_resp = resp_A if resp_A.status_code == 201 else resp_B
    conflict_resp = resp_A if resp_A.status_code == 409 else resp_B
    assert conflict_resp.json()["error"]["code"] == "SLOT_UNAVAILABLE"
    assert winner_resp.json()["status"] == "BOOKED"


@pytest.mark.asyncio
async def test_slot_hold_and_collision(async_client):
    """Test reserving a slot with /hold endpoint and attempting to book held slot by another patient."""
    admin_reg = {"email": "admin.hold@healthy.com", "password": "AdminPassword123!", "full_name": "Admin Hold", "role": "ADMIN"}
    await async_client.post("/api/auth/register", json=admin_reg)
    admin_login = await async_client.post("/api/auth/login", json={"email": "admin.hold@healthy.com", "password": "AdminPassword123!"})
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}

    monday_date = "2026-08-24"
    doc_req = {
        "email": "dr.hold@healthy.com",
        "password": "DocPassword123!",
        "full_name": "Dr. Hold Tester",
        "specialisation": "Dermatology",
        "slot_duration_minutes": 30,
        "working_hours": [
            {"day_of_week": 0, "start_time": "10:00:00", "end_time": "12:00:00"}
        ]
    }
    doc_resp = await async_client.post("/api/admin/doctors", json=doc_req, headers=admin_headers)
    assert doc_resp.status_code == 201
    doctor_id = doc_resp.json()["id"]

    # Register Patient A & B
    await async_client.post("/api/auth/register", json={"email": "holdA@test.com", "password": "PassA123!", "full_name": "Hold A", "role": "PATIENT"})
    loginA = await async_client.post("/api/auth/login", json={"email": "holdA@test.com", "password": "PassA123!"})
    headersA = {"Authorization": f"Bearer {loginA.json()['access_token']}"}

    await async_client.post("/api/auth/register", json={"email": "holdB@test.com", "password": "PassB123!", "full_name": "Patient B", "role": "PATIENT"})
    loginB = await async_client.post("/api/auth/login", json={"email": "holdB@test.com", "password": "PassB123!"})
    headersB = {"Authorization": f"Bearer {loginB.json()['access_token']}"}

    hold_payload = {
        "doctor_id": doctor_id,
        "appointment_date": monday_date,
        "start_time": "10:00:00",
        "end_time": "10:30:00"
    }

    # Patient A holds slot 10:00-10:30
    hold_resp = await async_client.post("/api/appointments/hold", json=hold_payload, headers=headersA)
    assert hold_resp.status_code == 201
    assert hold_resp.json()["status"] == "HELD"

    # Patient B tries to hold or book SAME slot -> receives 409 SLOT_UNAVAILABLE
    book_payload_B = {**hold_payload, "symptoms": "Skin rash"}
    conflict_resp = await async_client.post("/api/appointments", json=book_payload_B, headers=headersB)
    assert conflict_resp.status_code == 409
    assert conflict_resp.json()["error"]["code"] == "SLOT_UNAVAILABLE"
